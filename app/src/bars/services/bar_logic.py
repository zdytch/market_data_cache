from bars.models import BarSet, Bar
from common.schemas import Interval
from config.db import DB
from instruments import services as instrument_services
from ib.connector import ibc
from datetime import timedelta
from loguru import logger
from . import bar_crud, bar_interval_crud, bar_interval_logic


async def get_historical_bars(db: DB, bar_set: BarSet, interval: Interval) -> list[Bar]:
    existing_intervals = await bar_interval_crud.get_bar_intervals(db, bar_set)
    missing_intervals = bar_interval_logic.calculate_missing_intervals(
        interval, existing_intervals
    )
    missing_intervals = bar_interval_logic.split_intervals(
        missing_intervals, bar_set.timeframe, 100
    )
    instrument = bar_set.instrument
    live_bar = None

    for missing_interval in missing_intervals:
        is_overlap_session = await instrument_services.is_overlap_open_session(
            db, instrument, missing_interval
        )
        latest_ts = await bar_crud.get_latest_timestamp(db, bar_set)

        # If missing interval doesn't overlap with open session interval
        if not is_overlap_session:
            # Extend missing interval to overlap possible gaps in db
            missing_interval.start -= timedelta(days=1, seconds=1)
            missing_interval.end += timedelta(days=1, seconds=1)

        logger.debug(
            f'Missing bars within interval. Retreiving from origin... '
            f'{instrument.exchange}:{instrument.symbol}, {bar_set.timeframe}, {missing_interval}'
        )

        origin_bars = await _get_bars_from_origin(bar_set, missing_interval)

        if (
            is_overlap_session
            and origin_bars
            and latest_ts
            and latest_ts < origin_bars[-1].timestamp
        ):
            live_bar = origin_bars[-1]
            origin_bars.remove(live_bar)

        await bar_crud.bulk_save_bars(db, bar_set, origin_bars)

    bars = await bar_crud.get_bars(db, bar_set, interval)
    if live_bar:
        bars.append(live_bar)

    return bars


async def _get_bars_from_origin(bar_set: BarSet, interval: Interval) -> list[Bar]:
    bars = await ibc.get_historical_bars(bar_set, interval)
    instrument = bar_set.instrument

    if bars:
        logger.debug(
            f'Received bars from origin. '
            f'{instrument.exchange}:{instrument.symbol}, {bar_set.timeframe}, {interval}'
        )
    else:
        logger.debug(
            f'No bars from origin. '
            f'{instrument.exchange}:{instrument.symbol}, {bar_set.timeframe}, {interval}'
        )

    return bars
