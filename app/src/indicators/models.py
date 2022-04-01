from common.models import DBModel
from sqlmodel import Field, Column, DateTime, ForeignKey, Relationship
from sqlalchemy import UniqueConstraint
from bars.models import BarSet
from uuid import UUID
from decimal import Decimal
from datetime import datetime
import pytz


class Indicator(DBModel, table=True):
    bar_set_id: UUID = Field(
        sa_column=Column(ForeignKey('barset.id', ondelete='CASCADE'), nullable=False)
    )
    bar_set: BarSet = Relationship()
    length: int
    atr: Decimal = Decimal('0.0')
    valid_until: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: pytz.utc.localize(datetime.min),
    )

    __table_args__ = (UniqueConstraint('bar_set_id', 'length'),)
