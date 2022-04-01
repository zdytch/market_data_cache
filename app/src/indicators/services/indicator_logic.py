from indicators.models import Indicator
from bars.models import Timeframe, Bar
from config.db import DB
from instruments.models import Exchange
from instruments import services as instrument_services
from bars import services as bar_services
from common.schemas import Interval
from common.utils import round_with_quantum
from datetime import datetime, time, timedelta
from decimal import Decimal
import pytz
from . import indicator_crud


async def get_indicator(
    db: DB, symbol: str, exchange: Exchange, length: int
) -> Indicator:
    instrument = await instrument_services.get_saved_instrument(db, symbol, exchange)
    bar_set = await bar_services.get_bar_set(db, instrument, Timeframe.DAY)
    indicator = await indicator_crud.get_or_create_indicator(
        db, bar_set=bar_set, length=length
    )

    now = datetime.now(pytz.utc)
    if indicator.valid_until <= now:
        end = pytz.utc.localize(datetime.combine(now.date(), time(0, 0)))
        if await instrument_services.is_session_open(db, instrument):
            end -= timedelta(days=1)
        start = end - timedelta(days=30)  # TODO Better approach
        interval = Interval(start=start, end=end)

        bars = await bar_services.get_bars(db, bar_set, interval)
        trading_session = await instrument_services.get_nearest_trading_session(
            db, instrument
        )

        indicator.atr = _calculate_atr(bars, length)
        indicator.valid_until = trading_session.end

        await db.commit()

    return indicator


def _calculate_atr(bars: list[Bar], length: int) -> Decimal:
    atr = Decimal('0.0')

    if 0 < length < len(bars):
        source_bars = sorted(bars, key=lambda bar: bar.timestamp, reverse=True)
        true_ranges = []
        for index, bar in enumerate(source_bars[: length - 1]):
            true_range_option1 = bar.high - bar.low
            true_range_option2 = abs(bar.high - source_bars[index + 1].close)
            true_range_option3 = abs(bar.low - source_bars[index + 1].close)
            true_range = max(true_range_option1, true_range_option2, true_range_option3)
            true_ranges.append(true_range)

        atr = round_with_quantum(
            Decimal(sum(true_ranges) / len(true_ranges)), Decimal('0.0001')
        )

    return atr
