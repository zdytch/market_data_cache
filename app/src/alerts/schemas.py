from pydantic import BaseModel
from decimal import Decimal


class AlertBase(BaseModel):
    price: Decimal


class AlertGet(AlertBase):
    external_id: str


class AlertCreate(AlertGet):
    ticker: str


class AlertUpdate(AlertBase):
    pass
