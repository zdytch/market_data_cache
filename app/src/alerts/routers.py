from fastapi import APIRouter, Response, HTTPException, Depends
from config.db import DB, get_db
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from . import services
from .schemas import AlertCreate, AlertGet, AlertUpdate

alert_router = APIRouter(tags=['Alerts'])


@alert_router.post('', response_model=AlertGet, status_code=201)
async def create_alert(schema: AlertCreate, db: DB = Depends(get_db)):
    try:
        return await services.create_alert(
            db, schema.ticker, schema.external_id, schema.price
        )

    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f'Instrument with ticker {schema.ticker} not found',
        )

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=(
                f'Alert with price {schema.price} or external id {schema.external_id} '
                f'already exists for ticker {schema.ticker}'
            ),
        )


@alert_router.post('/bulk', response_model=AlertGet, status_code=201)
async def bulk_create_alerts(schemas: list[AlertCreate], db: DB = Depends(get_db)):
    try:
        await services.bulk_create_alerts(db, schemas)

    except NoResultFound:
        pass

    except IntegrityError:
        pass


@alert_router.put('/{external_id}', response_model=AlertGet)
async def update_alert(external_id: str, schema: AlertUpdate, db: DB = Depends(get_db)):
    try:
        return await services.update_alert(db, external_id, schema.price)

    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f'Alert with external_id {external_id} not found'
        )

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f'Another alert with price {schema.price} already exists',
        )


@alert_router.delete('/{external_id}', status_code=204, response_class=Response)
async def delete_alert(external_id: str, db: DB = Depends(get_db)):
    try:
        await services.delete_alert(db, external_id)

    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f'Alert with external_id {external_id} not found'
        )


@alert_router.delete('', status_code=204, response_class=Response)
async def delete_all_alerts(db: DB = Depends(get_db)):
    await services.bulk_delete_alerts(db)
