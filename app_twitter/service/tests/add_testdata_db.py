import datetime
import os

from dotenv import load_dotenv

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool

from models.models import metadata, Users, Followers, Tweets
from logger.logger import logger


async def add_test_data_in_db():
    TEST_USERS = 3
    APIKEYS = ["zero_user", "key1", "key2", "key3"]

    load_dotenv()

    DB_USER = os.environ.get("DB_USER", "default_value")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "default_value")
    DB_HOST = os.environ.get("DB_HOST", "default_value")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "default_value")
    ADD_TEST_DATA = os.environ.get("ADD_TEST_DATA", "no")

    if ADD_TEST_DATA != "yes":
        logger.info(f"Test data add interrupted. DB_NAME={DB_NAME}, ADD_TEST_DATA={ADD_TEST_DATA}")
        return False

    TEST_DB_URL = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:"
        f"{DB_PORT}/{DB_NAME}"
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

    session = async_session_maker()

    try:
        async with engine_test.begin() as conn:
            await conn.run_sync(metadata.drop_all)
        logger.info("...clear test database")

        async with engine_test.begin() as conn:
            await conn.run_sync(metadata.create_all)
        logger.info("...create test database")

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
    except Exception as e:
        logger.info(f"Data add with error.")
    logger.info("Data add complete.")
