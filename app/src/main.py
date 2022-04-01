from fastapi import FastAPI
from config import settings, db
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from routers import api_router
from ib.services import connect_brokers
import debugpy


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(api_router, prefix=settings.API_URL_PREFIX)

add_pagination(app)


@app.on_event('startup')
async def startup():
    await db.init_db()

    await connect_brokers()

    if settings.DEBUG:
        debugpy.listen(('0.0.0.0', 8888))
