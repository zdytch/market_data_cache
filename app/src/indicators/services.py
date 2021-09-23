from .models import Indicator
from bars.models import Timeframe, Bar
from instruments import services as instrument_services
from bars import services as bar_services
from common.schemas import Range
from common.utils import round_with_quantum
from datetime import datetime, time, timedelta
from decimal import Decimal
import pytz


async def get_indicator(ticker: str, length: int) -> Indicator:
    instrument = await instrument_services.get_instrument(ticker)
    bar_set = await bar_services.get_bar_set(instrument, Timeframe.DAY)
    indicator = await Indicator.objects.get_or_create(bar_set=bar_set, length=length)

    now = datetime.now(pytz.utc)
    if indicator.valid_until <= now:
        to_dt = pytz.utc.localize(datetime.combine(now.date(), time(0, 0)))
        if await instrument_services.is_session_open(instrument):
            to_dt -= timedelta(days=1)
        from_dt = to_dt - timedelta(days=30)  # TODO Better approach
        range = Range(from_t=int(from_dt.timestamp()), to_t=int(to_dt.timestamp()))

        bars = await bar_services.get_bars(bar_set, range)
        session = await instrument_services.get_session(instrument)

        indicator.atr = _calculate_atr(bars, length)
        indicator.valid_until = datetime.fromtimestamp(session.close_t, pytz.utc)

    return indicator


def _calculate_atr(bars: list[Bar], length: int) -> Decimal:
    atr = Decimal('0.0')

    if 0 < length < len(bars):
        source_bars = sorted(bars, key=lambda bar: bar.t, reverse=True)
        true_ranges = []
        for index, bar in enumerate(source_bars[: length - 1]):
            true_range_option1 = bar.h - bar.l
            true_range_option2 = abs(bar.h - source_bars[index + 1].c)
            true_range_option3 = abs(bar.l - source_bars[index + 1].c)
            true_range = max(true_range_option1, true_range_option2, true_range_option3)
            true_ranges.append(true_range)

        atr = round_with_quantum(
            Decimal(sum(true_ranges) / len(true_ranges)), Decimal('0.0001')
        )

    return atr