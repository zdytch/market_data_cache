from schemas import (
    Timeframe,
    Exchange,
    Bar,
    ChartData,
    Range,
    Instrument,
    BarList,
)
from ib_connector import IBConnector
from datetime import datetime
import pytz
import cache
from loguru import logger

ibc = IBConnector()


async def get_instrument(ticker: str) -> Instrument:
    exchange, symbol = tuple(ticker.split(':'))
    exchange = Exchange(exchange)

    try:
        instrument = await cache.get_instrument(symbol, exchange)
    except:
        try:
            instrument = await _get_instrument_from_origin(symbol, exchange)
            await cache.save_instrument(instrument)

        except Exception as e:
            logger.debug(e)

    return instrument


async def get_bar_list(
    ticker: str, timeframe: Timeframe, from_t: int, to_t: int
) -> BarList:
    instrument = await get_instrument(ticker)
    range = Range(from_t=from_t, to_t=to_t)

    cache_ranges = await cache.get_ranges(instrument, timeframe)
    missing_ranges = _calculate_missing_ranges(range, cache_ranges)

    for missing_range in missing_ranges:
        logger.debug(
            f'Missing bars in cache. Retreiving from origin... Instrument: {instrument}. Range: {missing_range}'
        )

        try:
            origin_bars = await _get_bars_from_origin(
                instrument, timeframe, missing_range
            )
            await cache.save_bars(instrument, timeframe, missing_range, origin_bars)
        except Exception as e:
            logger.debug(e)

    bars = await cache.get_bars(instrument, timeframe, range)

    return BarList(instrument=instrument, timeframe=timeframe, bars=bars)


async def bar_list_to_chart_data(data: BarList) -> ChartData:
    chart_data = ChartData()

    for bar in data.bars:
        chart_data.o.append(bar.o)
        chart_data.h.append(bar.h)
        chart_data.l.append(bar.l)
        chart_data.c.append(bar.c)
        chart_data.v.append(bar.v)
        chart_data.t.append(bar.t)

    if data.bars:
        chart_data.s = 'ok'
    else:
        last_ts = await cache.get_last_timestamp(data.instrument, data.timeframe)
        chart_data.next_time = last_ts

    return chart_data


async def _get_instrument_from_origin(symbol: str, exchange: Exchange) -> Instrument:
    instrument = await ibc.get_instrument(symbol, exchange)

    logger.debug(f'Received instrument from origin: {instrument}')

    return instrument


async def _get_bars_from_origin(
    instrument: Instrument, timeframe: Timeframe, range: Range
) -> list[Bar]:
    from_dt = datetime.fromtimestamp(range.from_t, pytz.utc)
    to_dt = datetime.fromtimestamp(range.to_t, pytz.utc)

    bars = await ibc.get_historical_bars(instrument, timeframe, from_dt, to_dt)

    if bars:
        logger.debug(
            f'Received bars from origin. Instrument: {instrument}. Range: {range}'
        )
    else:
        logger.debug(f'No bars from origin. Instrument: {instrument}. Range: {range}')

    return bars


def _calculate_missing_ranges(
    within_range: Range, existing_ranges: list[Range]
) -> list:
    missing_ranges = []
    next_from_t = within_range.from_t

    for range in existing_ranges:
        if range.to_t > within_range.from_t and range.from_t < within_range.to_t:
            if range.from_t > next_from_t < within_range.to_t:
                missing_ranges.append(Range(from_t=next_from_t, to_t=range.from_t))

            next_from_t = range.to_t

    if next_from_t < within_range.to_t:
        missing_ranges.append(Range(from_t=next_from_t, to_t=within_range.to_t))

    return missing_ranges


def _is_session_open(instrument: Instrument):
    return (
        instrument.nearest_session.open_t
        <= int(datetime.now(pytz.utc).timestamp())
        < instrument.nearest_session.close_t
    )


def _is_session_up_to_date(instrument: Instrument):
    instrument.nearest_session.close_t > int(datetime.now(pytz.utc).timestamp())
