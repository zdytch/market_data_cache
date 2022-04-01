import os
from loguru import logger


DEBUG = int(os.environ['APP_DEBUG'])

API_URL_PREFIX = '/api/v1'

SECRET_KEY = os.environ['APP_SECRET_KEY']

DB_URL = (
    f'postgresql+asyncpg://{os.getenv("POSTGRES_USER")}:'
    f'{os.getenv("POSTGRES_PASSWORD")}@'
    f'mdc-db:5432/'
    f'{os.getenv("POSTGRES_DB")}'
)

BACKEND_CORS_ORIGINS = [
    'http://localhost:3000',
]

TELEGRAM_TOKEN = os.environ['APP_TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['APP_TELEGRAM_CHAT_ID']

logger.add(
    'logs/mdc_{time}.log',
    format='{time} {level} {message}',
    level='DEBUG',
    rotation='100 MB',
    retention='14 days',
    compression='zip',
)
