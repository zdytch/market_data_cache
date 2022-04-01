from instruments.models import Instrument, TradingSession
from common.schemas import Interval
from config.db import DB
from ib.connector import ibc
from datetime import datetime
import pytz
from . import trading_session_crud


async def get_nearest_trading_session(db: DB, instrument: Instrument) -> TradingSession:
    trading_session = await trading_session_crud.get_or_create_trading_session(
        db, instrument
    )

    if not is_session_up_to_date(trading_session):
        info = await ibc.get_instrument_info(instrument.symbol, instrument.exchange)
        trading_session.start = info.nearest_session.start
        trading_session.end = info.nearest_session.end

        await db.commit()

    return trading_session


async def is_overlap_open_session(
    db: DB, instrument: Instrument, interval: Interval
) -> bool:
    trading_session = await get_nearest_trading_session(db, instrument)

    return (
        (interval.start >= trading_session.start and interval.end < trading_session.end)
        or interval.start < trading_session.start < interval.end
        or interval.start < trading_session.end < interval.end
    )


async def is_session_open(db: DB, instrument: Instrument) -> bool:
    trading_session = await get_nearest_trading_session(db, instrument)

    return trading_session.start <= datetime.now(pytz.utc) < trading_session.end


def is_session_up_to_date(session: TradingSession) -> bool:
    return session.end > datetime.now(pytz.utc)
