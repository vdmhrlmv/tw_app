import os
from typing import AsyncGenerator
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from logger.logger import logger

load_dotenv()

DB_USER = os.environ.get("DB_USER", "default_value")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "default_value")
DB_HOST = os.environ.get("DB_HOST", "default_value")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "default_value")


logger.info(f"DB NAME = {DB_NAME}")

engine = create_async_engine(
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    poolclass=NullPool,
    echo=False,
)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Dependency
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
