from .schemas import History, Info, SearchResult, Config
from config.db import DB
from bars.models import Timeframe
from common.schemas import Interval
from bars import services as bar_services
from instruments.models import Exchange, InstrumentType
from instruments import services as instrument_services
from datetime import datetime
from loguru import logger
import pytz


async def get_history(
    db: DB, ticker: str, timeframe: str, from_t: int, to_t: int
) -> History:
    history = History()
    bars = []
    next_time = 0

    try:
        exchange, symbol = instrument_services.split_ticker(ticker)
        instrument = await instrument_services.get_saved_instrument(
            db, symbol, exchange
        )
        bar_set = await bar_services.get_bar_set(db, instrument, Timeframe(timeframe))

        start = datetime.fromtimestamp(from_t, pytz.utc)
        end = datetime.fromtimestamp(to_t, pytz.utc)
        interval = Interval(start=start, end=end)
        bars = await bar_services.get_historical_bars(db, bar_set, interval)

        latest_ts = await bar_services.get_latest_timestamp(db, bar_set)
        next_time = int(latest_ts.timestamp())

    except ConnectionRefusedError as error:
        logger.error(error)

    for bar in bars:
        history.o.append(bar.open)
        history.h.append(bar.high)
        history.l.append(bar.low)
        history.c.append(bar.close)
        history.v.append(bar.volume)
        history.t.append(int(bar.timestamp.timestamp()))

    if bars:
        history.s = 'ok'
    elif next_time > 0:
        history.nextTime = next_time

    return history


async def get_info(db: DB, ticker: str) -> Info:
    info = Info(name=ticker, ticker=ticker)

    try:
        exchange, symbol = instrument_services.split_ticker(ticker)
        instrument = await instrument_services.get_saved_instrument(
            db, symbol, exchange
        )
        instrument_type = _instrument_type_to_chart(instrument.type)
        timezone, session = _exchange_schedule_to_chart(instrument.exchange)
        price_scale = 10 ** abs(instrument.tick_size.normalize().as_tuple().exponent)
        min_movement = int(instrument.tick_size * price_scale)

        info.type = instrument_type
        info.description = instrument.description
        info.exchange = instrument.exchange.value
        info.listed_exchange = instrument.exchange.value
        info.session = session
        info.timezone = timezone
        info.minmov = min_movement
        info.pricescale = price_scale

    except ConnectionRefusedError as error:
        logger.error(error)

    return info


async def get_search_results(search: str) -> list[SearchResult]:
    results = []
    instruments = await instrument_services.search_broker_instruments(search)

    for instrument in instruments:
        ticker = f'{instrument.exchange}:{instrument.symbol}'
        result = SearchResult(
            symbol=ticker,
            full_name=ticker,
            ticker=ticker,
            description=instrument.description,
            exchange=str(instrument.exchange),
            type=_instrument_type_to_chart(instrument.type),
        )
        results.append(result)

    return results


def get_config() -> Config:
    return Config(
        supported_resolutions=['1', '5', '30', '60', '1D'],
        supports_search=True,
        supports_group_request=False,
        supports_marks=False,
        supports_timescale_marks=False,
    )


def _instrument_type_to_chart(type: InstrumentType) -> str:
    if type == InstrumentType.STOCK:
        instrument_type = 'stock'
    elif type == InstrumentType.FUTURE:
        instrument_type = 'futures'
    else:
        raise ValueError(f'Cannot convert {type} to InstrumentType')

    return instrument_type


def _exchange_schedule_to_chart(exchange: Exchange) -> tuple[str, str]:
    if exchange in (Exchange.NASDAQ, Exchange.NYSE):
        tz_id = 'America/New_York'
        session = '0930-1600'
    elif exchange == Exchange.NYMEX:
        tz_id = 'America/New_York'
        session = '1800-1700'
    elif exchange in (Exchange.GLOBEX, Exchange.ECBOT):
        tz_id = 'America/Chicago'
        session = '1700-1600'
    else:
        raise ValueError(f'Cannot get schedule for exchange {exchange}')

    return tz_id, session
