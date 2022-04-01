from instruments.models import Instrument, Exchange
from config.db import DB
from sqlalchemy.orm.exc import NoResultFound
from ib.connector import ibc
from . import instrument_crud


async def get_saved_instrument(db: DB, symbol: str, exchange: Exchange) -> Instrument:
    try:
        instrument = await instrument_crud.get_instrument(
            db,
            symbol=symbol,
            exchange=exchange,
        )

    except NoResultFound:
        info = await ibc.get_instrument_info(symbol, exchange)
        instrument = await instrument_crud.create_instrument(
            db,
            info.symbol,
            info.ib_symbol,
            info.exchange,
            info.type,
            info.description,
            info.tick_size,
            info.multiplier,
        )

    return instrument


async def search_broker_instruments(symbol: str) -> list[Instrument]:
    instruments = []
    infos = await ibc.search_instrument_info(symbol)

    for info in infos:
        instrument = Instrument(
            symbol=info.symbol,
            ib_symbol=info.ib_symbol,
            exchange=info.exchange,
            type=info.type,
            description=info.description,
            tick_size=info.tick_size,
            multiplier=info.multiplier,
        )
        instruments.append(instrument)

    return instruments


def split_ticker(ticker: str) -> tuple[Exchange, str]:
    exchange, symbol = tuple(ticker.split(':'))
    exchange = Exchange(exchange)

    return (exchange, symbol)
