from ..models import Alert
from ..schemas import AlertCreate
from config.db import DB
from sqlmodel import select, insert, delete
from sqlalchemy.orm import joinedload
from instruments.models import Instrument
from instruments import services as instrument_services
from decimal import Decimal


async def get_alert_list(db: DB, **kwargs) -> list[Alert]:
    query = select(Alert).filter_by(**kwargs).options(joinedload(Alert.instrument))

    return (await db.execute(query)).scalars().all()


async def create_alert(db: DB, ticker: str, external_id: str, price: Decimal) -> Alert:
    exchange, symbol = instrument_services.split_ticker(ticker)
    instrument = await instrument_services.get_saved_instrument(db, symbol, exchange)

    alert = Alert(instrument_id=instrument.id, external_id=external_id, price=price)
    db.add(alert)
    await db.commit()

    return alert


async def bulk_create_alerts(db: DB, alert_schemas: list[AlertCreate]) -> None:
    instruments = (await db.execute(select(Instrument))).scalars().all()
    alert_dicts = [alert.dict(exclude_none=True) for alert in alert_schemas]
    alerts_to_create = []

    for alert_dict in alert_dicts:
        ticker = alert_dict.pop('ticker')
        exchange, symbol = instrument_services.split_ticker(ticker)
        instrument = next(
            (i for i in instruments if i.symbol == symbol and i.exchange == exchange),
            None,
        )

        if instrument:
            alert_dict['instrument_id'] = instrument.id
            alerts_to_create.append(alert_dict)

    await db.execute(insert(Alert).values(alerts_to_create))
    await db.commit()


async def get_alert(db: DB, **kwargs) -> Alert:
    result = await db.execute(select(Alert).filter_by(**kwargs))

    return result.unique().scalar_one()


async def update_alert(db: DB, external_id: str, price: Decimal) -> Alert:
    alert = await get_alert(db, external_id=external_id)
    alert.price = price
    await db.commit()

    return alert


async def delete_alert(db: DB, external_id: str) -> None:
    alert = await get_alert(db, external_id=external_id)

    await db.delete(alert)
    await db.commit()


async def bulk_delete_alerts(db: DB, **kwargs) -> None:
    query = delete(Alert).filter_by(**kwargs)

    await db.execute(query)
    await db.commit()
