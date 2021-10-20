from config.db import Base
from common.models import BaseMixin
from sqlalchemy import (
    Column,
    String,
    Numeric,
    Enum as EnumField,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from enum import Enum


class Exchange(str, Enum):
    NYSE = 'NYSE'
    NASDAQ = 'NASDAQ'
    GLOBEX = 'GLOBEX'
    NYMEX = 'NYMEX'
    ECBOT = 'ECBOT'


class InstrumentType(str, Enum):
    STOCK = 'STK'
    FUTURE = 'FUT'


class Instrument(Base, BaseMixin):
    symbol = Column(String(8), nullable=False)
    ib_symbol = Column(String(8), nullable=False)
    exchange = Column(EnumField(Exchange), nullable=False)
    type = Column(EnumField(InstrumentType), nullable=False)
    description = Column(String(64), nullable=False)
    tick_size = Column(Numeric(), nullable=False)
    multiplier = Column(Numeric(), nullable=False)

    __table_args__ = (UniqueConstraint('symbol', 'exchange'),)


class TradingSession(Base, BaseMixin):
    instrument_id = Column(ForeignKey('instrument.id'))
    open_dt = Column(DateTime(timezone=True), nullable=False)
    close_dt = Column(DateTime(timezone=True), nullable=False)

    instrument = relationship('Instrument', backref='sessions')
