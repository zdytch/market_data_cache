from fastapi import APIRouter, HTTPException, Depends
from config.db import DB, get_db
from .schemas import IndicatorGet
from . import services
from instruments import services as instrument_services

indicator_router = APIRouter(tags=['Indicators'])


@indicator_router.get('/{ticker}', response_model=IndicatorGet)
async def get_indicator(
    ticker: str,
    length: int,
    db: DB = Depends(get_db),
):
    try:
        exchange, symbol = instrument_services.split_ticker(ticker)
        return await services.get_indicator(db, symbol, exchange, length)

    except:  # TODO: catch business exception
        raise HTTPException(
            status_code=404,
            detail=f'Instrument with ticker {ticker} not found',
        )
