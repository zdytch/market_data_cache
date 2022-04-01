from pydantic import BaseModel
from instruments.models import Exchange, InstrumentType
from common.schemas import Interval
from decimal import Decimal
from datetime import datetime


class InstrumentInfo(BaseModel):
    symbol: str
    ib_symbol: str
    exchange: Exchange
    type: InstrumentType
    description: str
    tick_size: Decimal
    multiplier: Decimal
    nearest_session: Interval


class BarInfo(BaseModel):
    symbol: str
    exchange: Exchange
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    timestamp: datetime
