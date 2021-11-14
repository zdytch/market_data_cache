from typing import Optional
from pydantic import BaseModel
from .models import InstrumentType
from datetime import datetime
from decimal import Decimal


class InstrumentGet(BaseModel):
    symbol: str
    exchange: str
    type: InstrumentType
    description: str
    tick_size: Decimal
    multiplier: Decimal
    sector: Optional[str]
    industry: Optional[str]

    class Config:
        orm_mode = True


class InstrumentList(InstrumentGet):
    pass


class SessionGet(BaseModel):
    start: datetime
    end: datetime

    class Config:
        orm_mode = True
