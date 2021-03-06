from instruments.models import Exchange, InstrumentType
from bars.models import Timeframe
from common.schemas import Interval
from datetime import datetime, date, time
import math
import pytz


def timeframe_to_ib(timeframe: Timeframe) -> str:
    if timeframe == Timeframe.DAY:
        ib_timeframe = '1 day'
    elif timeframe == Timeframe.M60:
        ib_timeframe = '1 hour'
    elif timeframe == Timeframe.M30:
        ib_timeframe = '30 mins'
    elif timeframe == Timeframe.M5:
        ib_timeframe = '5 mins'
    elif timeframe == Timeframe.M1:
        ib_timeframe = '1 min'
    else:
        raise ValueError(f'Cannot convert {timeframe} to IB timeframe')

    return ib_timeframe


def duration_to_ib(start: datetime, end: datetime) -> str:
    total_seconds = int((end - start).total_seconds())
    total_days = math.ceil(total_seconds / 86400)  # Seconds in day
    total_years = math.ceil(total_days / 365)  # Days in year

    if total_seconds < 86400:
        # TWS requires duration to be at least 30 seconds
        total_seconds = total_seconds if total_seconds >= 30 else 30
        duration = f'{total_seconds} S'
    elif total_days < 365:
        duration = f'{total_days} D'
    else:
        duration = f'{total_years} Y'

    return duration


def timestamp_from_ib(dt: datetime | date) -> datetime:
    if type(dt) is date:
        date_time = pytz.utc.localize(datetime.combine(dt, time(0, 0)))
    elif type(dt) is datetime:
        date_time = dt
    else:
        raise ValueError(f'Cannot convert datetime {dt} from IB')

    return date_time


def get_instrument_type_by_exchange(exchange: Exchange) -> InstrumentType:
    if exchange in (Exchange.NASDAQ, Exchange.NYSE):
        instrument_type = InstrumentType.STOCK
    elif exchange in (Exchange.GLOBEX, Exchange.ECBOT, Exchange.NYMEX):
        instrument_type = InstrumentType.FUTURE
    else:
        raise ValueError(f'Cannot get instrument type, exchange unknown: {exchange}')

    return instrument_type


def security_type_to_ib(
    exchange: Exchange | None, instrument_type: InstrumentType | None
) -> str:
    if exchange and not instrument_type:
        instrument_type = get_instrument_type_by_exchange(exchange)

    if instrument_type == InstrumentType.STOCK:
        sec_type = 'STK'
    elif instrument_type == InstrumentType.FUTURE:
        sec_type = 'CONTFUT'
    else:
        raise ValueError(
            f'Cannot get security type, instrument type unknown: {instrument_type}'
        )

    return sec_type


def get_nearest_trading_interval(trading_hours: str, tz_id: str) -> Interval:
    min_dt = pytz.utc.localize(datetime.min)
    nearest_interval = Interval(start=min_dt, end=min_dt)
    session_tz = pytz.timezone(tz_id)

    for ib_session in trading_hours.split(';'):
        if ib_session and not 'CLOSED' in ib_session:
            ib_open, ib_close = tuple(ib_session.split('-'))
            open = session_tz.localize(datetime.strptime(ib_open, '%Y%m%d:%H%M'))
            close = session_tz.localize(datetime.strptime(ib_close, '%Y%m%d:%H%M'))
            if close > datetime.now(pytz.utc):
                nearest_interval.start = open
                nearest_interval.end = close
                break

    return nearest_interval
