from common.models import DBModel
from sqlmodel import Field, Column, ForeignKey, Relationship
from sqlalchemy import UniqueConstraint
from instruments.models import Instrument
from uuid import UUID
from decimal import Decimal


class Alert(DBModel, table=True):
    instrument_id: UUID = Field(
        sa_column=Column(
            ForeignKey('instrument.id', ondelete='CASCADE'), nullable=False
        )
    )
    instrument: Instrument = Relationship()
    external_id: int
    price: Decimal

    __table_args__ = (UniqueConstraint('instrument_id', 'price'),)