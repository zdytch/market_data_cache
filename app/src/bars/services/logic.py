from bars.models import BarSet, Bar, BarRange, Timeframe
from instruments.models import Instrument
from instruments import services as instrument_services
from common.schemas import Range
from . import crud
from ib.connector import ib_connector
from loguru import logger


async def get_bar_set(instrument: Instrument, timeframe: Timeframe) -> BarSet:
    return await BarSet.objects.select_related('instrument').get_or_create(
        instrument=instrument, timeframe=timeframe
    )


async def get_bars(bar_set: BarSet, range: Range) -> list[Bar]:
    existing_ranges = await BarRange.objects.filter(bar_set=bar_set).all()
    missing_ranges = _calculate_missing_ranges(range, existing_ranges)
    instrument = bar_set.instrument
    live_bar = None

    for missing_range in missing_ranges:
        is_overlap_session = await instrument_services.is_overlap_open_session(
            instrument, missing_range
        )

        # If missing range doesn't overlap with open session range
        if not is_overlap_session:
            # Extend missing range by (1 day + 1 sec) to overlap possible gaps in db
            missing_range.from_t -= 86401
            missing_range.to_t += 86401

        logger.debug(
            f'Missing bars in range. Retreiving from origin... '
            f'{instrument.exchange}:{instrument.symbol}, {bar_set.timeframe}, {missing_range}'
        )

        try:
            origin_bars = await _get_bars_from_origin(bar_set, missing_range)

            if (
                is_overlap_session
                and origin_bars
                and await get_latest_timestamp(bar_set) < origin_bars[-1].t
            ):
                live_bar = origin_bars[-1]
                origin_bars.remove(live_bar)

            await crud.add_bars(bar_set, origin_bars)

        except Exception as e:
            logger.debug(e)

    bars = await crud.get_bars(bar_set, range)
    if live_bar:
        bars.append(live_bar)

    return bars


async def get_latest_timestamp(bar_set: BarSet) -> int:
    return await Bar.objects.filter(bar_set=bar_set).max('t') or 0


async def _get_bars_from_origin(bar_set: BarSet, range: Range) -> list[Bar]:
    bars = await ib_connector.get_historical_bars(bar_set, range)
    instrument = bar_set.instrument

    if bars:
        logger.debug(
            f'Received bars from origin. '
            f'{instrument.exchange}:{instrument.symbol}, {bar_set.timeframe}, {range}'
        )
    else:
        logger.debug(
            f'No bars from origin. '
            f'{instrument.exchange}:{instrument.symbol}, {bar_set.timeframe}, {range}'
        )

    return bars


def _calculate_missing_ranges(
    within_range: Range, existing_ranges: list[BarRange]
) -> list[Range]:
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
