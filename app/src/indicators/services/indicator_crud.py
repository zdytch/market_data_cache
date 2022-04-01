from indicators.models import Indicator
from bars.models import BarSet
from config.db import DB
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound


async def get_or_create_indicator(db: DB, bar_set: BarSet, length: int) -> Indicator:
    try:
        query = (
            select(Indicator)
            .filter_by(bar_set_id=bar_set.id, length=length)
            .options(joinedload(Indicator.bar_set))
        )
        indicator = (await db.execute(query)).scalar_one()

    except NoResultFound:
        indicator = Indicator(bar_set_id=bar_set.id, length=length)
        db.add(indicator)

        await db.commit()

    return indicator
