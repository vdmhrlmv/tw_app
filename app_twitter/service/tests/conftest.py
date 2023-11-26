import datetime
import os

import pytest_asyncio
from dotenv import load_dotenv
import asyncio
from httpx import AsyncClient

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator

from models.models import Base, metadata, Users, Followers, Tweets, Media, Likes
from logger.logger import logger
from main import app


TEST_USERS = 3
APIKEYS = ["zero_user", "key1", "key2", "key3"]

TWEETS = {1: [], 2: [], 3: []}

load_dotenv()

DB_USER = os.environ.get("DB_USER", "default_value")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "default_value")
DB_HOST = os.environ.get("DB_HOST", "default_value")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "default_value")
TESTING = os.environ.get("TESTING", "no")


if TESTING != "yes":
    logger.error(
        f"Testing interrupted, incorrect environment. DB_NAME={DB_NAME}, TESTING={TESTING}"
    )
    raise Exception("Testing interrupted, incorrect environment.")


logger.info("Conf test Start.")

TEST_DB_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:" f"{DB_PORT}/{DB_NAME}"
)

engine_test = create_async_engine(
    TEST_DB_URL,
    poolclass=NullPool,
    echo=False,
)


async_session_maker = sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)
metadata.bind = engine_test


@pytest_asyncio.fixture(autouse=True, scope="session")
async def prepare_database():
    logger.info("Prepare database for tests")
    async with engine_test.begin() as conn:
        await conn.run_sync(metadata.drop_all)
    logger.info("...clear test database")

    async with engine_test.begin() as conn:
        await conn.run_sync(metadata.create_all)
    logger.info("...create test database")


@pytest_asyncio.fixture(scope="session")
def event_loop():  # request
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="session")
async def init_test_data():
    logger.info("Init test data fixture.")
    session = async_session_maker()

    async with session.begin():
        for n in range(1, TEST_USERS + 1):
            new_user = Users(
                name=f"User_name_{n}",
                email=f"user{n}email@email.com",
                apikey=APIKEYS[n],
                last_activity=datetime.datetime.now(),
            )

            session.add(new_user)

        new_user = Users(
            name=f"test_User",
            email=f"user_test_email@email.com",
            apikey=f"test",
            last_activity=datetime.datetime.now(),
        )

        session.add(new_user)

    # 1user -> 2,3, 2user -> 3, 3user ->
    for n in range(1, TEST_USERS + 1):
        for f in range(n + 1, TEST_USERS + 1):
            new_follower = Followers(follower_id=f, user_id=n)
            async with session.begin():
                session.add(new_follower)

    for n in range(1, TEST_USERS + 1):
        for tw in range(1, 6):
            new_tweet = Tweets(
                tweetdata=f"test tweet number {tw} from user {n}", user_id=n
            )
            async with session.begin():
                session.add(new_tweet)
