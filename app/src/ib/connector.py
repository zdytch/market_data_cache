from ib_insync import IB, Contract, Stock, ContFuture
from instruments.schemas import Instrument, Exchange, InstrumentType
from bars.schemas import Bar, Timeframe
from datetime import datetime
from decimal import Decimal
from . import utils
from loguru import logger


class IBConnector:
    def __init__(self):
        self._ib = IB()
        self._ib.errorEvent += self._error_callback

    @property
    def is_connected(self) -> bool:
        return self._ib.isConnected()

    async def get_instrument(self, symbol: str, exchange: Exchange) -> Instrument:
        await self._connect()

        contract = await self._get_contract(symbol, exchange)
        type = utils.get_instrument_type_by_exchange(exchange)
        is_stock = type == InstrumentType.STOCK
        details = await self._ib.reqContractDetailsAsync(contract)
        description = details[0].longName
        tick_size = Decimal('0.01') if is_stock else Decimal(str(details[0].minTick))
        multiplier = Decimal('1.00') if is_stock else Decimal(str(contract.multiplier))
        trading_hours = details[0].liquidHours if is_stock else details[0].tradingHours
        nearest_session = utils.get_nearest_trading_session(
            trading_hours, details[0].timeZoneId
        )

        return Instrument(
            symbol=symbol,
            exchange=exchange,
            type=type,
            description=description,
            tick_size=tick_size,
            multiplier=multiplier,
            nearest_session=nearest_session,
        )

    async def get_historical_bars(
        self,
        instrument: Instrument,
        timeframe: Timeframe,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[Bar]:
        await self._connect()

        contract = await self._get_contract(instrument.symbol, instrument.exchange)
        is_stock = instrument.type == InstrumentType.STOCK
        volume_multiplier = 100 if is_stock else 1

        ib_bars = await self._ib.reqHistoricalDataAsync(
            contract=contract,
            endDateTime=to_dt,
            durationStr=utils.duration_to_ib(from_dt, to_dt),
            barSizeSetting=utils.timeframe_to_ib(timeframe),
            whatToShow='TRADES',
            useRTH=is_stock,
            formatDate=2,
            keepUpToDate=False,
        )

        bars = []
        for ib_bar in ib_bars:
            bar = utils.bar_from_ib(ib_bar, instrument.tick_size, volume_multiplier)
            if int(from_dt.timestamp()) <= bar.t <= int(to_dt.timestamp()):
                bars.append(bar)

        return bars

    async def _connect(self, client_id=14):
        if not self.is_connected:
            try:
                await self._ib.connectAsync('trixter-ib', 4002, client_id)
            except Exception as error:
                logger.error(error)

    async def _get_contract(self, symbol: str, exchange: Exchange) -> Contract:
        type = utils.get_instrument_type_by_exchange(exchange)
        if type == InstrumentType.STOCK:
            contract = Stock(symbol, f'SMART:{exchange}', 'USD')
        elif type == InstrumentType.FUTURE:
            contract = ContFuture(symbol, f'SMART:{exchange}', currency='USD')
        else:
            raise ValueError(
                f'Cannot get contract for type {type}, '
                f'symbol {symbol}, exchange {exchange}'
            )

        if contract:
            await self._ib.qualifyContractsAsync(contract)
            if not contract.conId:
                raise ValueError(f'Cannot qualify contract {contract}')

        return contract

    def _error_callback(
        self, req_id: int, error_code: int, error_string: str, contract: Contract
    ) -> None:
        logger.debug(f'{req_id} {error_code} {error_string} {contract}')


ib_connector = IBConnector()