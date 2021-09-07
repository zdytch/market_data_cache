from pydantic import BaseModel
from decimal import Decimal


class History(BaseModel):
    o: list[Decimal] = []
    h: list[Decimal] = []
    l: list[Decimal] = []
    c: list[Decimal] = []
    v: list[int] = []
    t: list[int] = []
    s: str = 'no_data'
    nextTime: int = 0


class Info(BaseModel):
    name: str
    ticker: str
    type: str
    description: str
    exchange: str
    listed_exchange: str
    session: str
    timezone: str
    currency_code: str
    has_daily: str
    has_intraday: str
    minmov: int
    pricescale: int


class Config(BaseModel):
    supported_resolutions: list[str]
    supports_search: bool
    supports_group_request: bool
    supports_marks: bool
    supports_timescale_marks: bool