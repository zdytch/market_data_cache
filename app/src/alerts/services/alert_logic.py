from config.db import DB
from ib.schemas import BarInfo
from . import alert_crud
from indicators import services as indicator_services
from config.settings import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from decimal import Decimal
import httpx


async def check_alerts(db: DB, bar_info: BarInfo):
    indicator = await indicator_services.get_indicator(
        db, bar_info.symbol, bar_info.exchange, 5
    )
    alerts = await alert_crud.get_alert_list(
        db, instrument_id=indicator.bar_set.instrument_id
    )
    atr = indicator.atr

    for alert in alerts:
        if (
            _is_near_price(bar_info, alert.price, atr * Decimal('0.15'))
            and not alert.is_triggered
        ):
            alert.is_triggered = True

            await _send_message(alert.external_id)

        elif (
            not _is_near_price(bar_info, alert.price, atr * Decimal('0.20'))
            and alert.is_triggered
        ):
            alert.is_triggered = False

    await db.commit()


def _is_near_price(bar_info: BarInfo, price: Decimal, tolerance: Decimal) -> bool:
    return price + tolerance >= bar_info.low and price - tolerance <= bar_info.high


async def _send_message(message: str):
    url = (
        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        f'?chat_id={TELEGRAM_CHAT_ID}&text={message}'
    )

    async with httpx.AsyncClient() as client:
        await client.get(url)
