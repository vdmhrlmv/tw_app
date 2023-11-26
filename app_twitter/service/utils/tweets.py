import datetime
from pprint import pprint
from typing import Any
from pathlib import Path, PurePath, PurePosixPath

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete


from logger.logger import logger
from models.models import Users, Followers, Tweets, Likes, Media
from .users import update_user_last_activity, check_user_exists
from .media import link_media_to_tweet, delete_media, MEDIA_DIR


async def add_tweet(
    session: AsyncSession, user_idx: int, tweet_data: str, tweet_media_ids: tuple
):
    """
    добавление твита
    :param session:
    :param tweet_data: текст твита
    :param tweet_media_ids: список id картинок добавленных к твиту
    :param user_idx: id пользователя создавшего твит
    :return: id созданного твита
    """

    try:
        res_insert_tweet = await session.execute(
            insert(Tweets)
            .values(tweetdata=tweet_data, user_id=user_idx)
            .returning(Tweets.id)
        )

        await update_user_last_activity(session, user_id=user_idx)
        await session.commit()

        tweet_id = res_insert_tweet.scalars().one()

        # если был передан media_id то привязывем строку с мадиаданными к твиту
        if len(tweet_media_ids) > 0:
            await link_media_to_tweet(session, tweet_media_ids, tweet_id)

        return tweet_id
    except Exception as err:
        logger.error(err)

    return None


async def tweets_list(session: AsyncSession, user_idx: int) -> list:
    """
    формирование ленты с твитами
    :param session: экземпляр сессии работы с БД
    :param user_idx: id пользователя
    :return: список твитов для пользователя
    """

    try:
        # получение списка id твитов в ленте
        query_tweets_id = (
            select(Tweets.id)
            .join(Users)
            .join(Followers)
            .where(Followers.follower_id == user_idx)
        )
        # получение списка лайков для ленты твитов
        query_likes_list = (
            select(Likes.user_id, Likes.tweet_id, Users.name)
            .join(Users)
            .where(Likes.tweet_id.in_(query_tweets_id))
        )

        res_likes_list = await session.execute(query_likes_list)
        likes = dict()
        for like in res_likes_list:
            if like.tweet_id in likes:
                likes[like.tweet_id].append(
                    {"user_id": like.user_id, "name": like.name}
                )
            else:
                likes[like.tweet_id] = [
                    {"user_id": like.user_id, "name": like.name},
                ]

        # подготовка списка прикрепленных медиа
        query_media = select(Media.id, Media.filepath, Media.tweet_id).where(
            Media.tweet_id.in_(query_tweets_id)
        )
        res = await session.execute(query_media)
        media_dict = dict()
        for media in res:
            if media.tweet_id in media_dict.keys():
                media_dict[media.tweet_id].append(
                    str(Path(Path(MEDIA_DIR).stem).joinpath(media.filepath))
                )
            else:
                media_dict[media.tweet_id] = [
                    str(Path(Path(MEDIA_DIR).stem).joinpath(media.filepath)),
                ]

        query_tweets = (
            select(Tweets.id, Tweets.tweetdata, Users.id, Users.name)
            .join(Users)
            .join(Followers)
            .where(Followers.follower_id == user_idx)
        )

        res = await session.execute(query_tweets)

        await update_user_last_activity(session, user_id=user_idx)
        await session.commit()

    except Exception as err:
        logger.error(err)

        return []

    result_tweet_list = list()
    for tweet in res:
        if tweet.id not in likes:
            likes[tweet.id] = []
        result_tweet_list.append(
            {
                "id": tweet.id,
                "content": tweet.tweetdata,
                "author": {"id": tweet.id_1, "name": tweet.name},
                "attachments": media_dict.get(tweet.id),
                "likes": likes[tweet.id],
            }
        )

    return result_tweet_list


async def check_tweet_exists(session: AsyncSession, tweet_idx: int) -> bool:
    """
    проверка существования твита
    :param session:
    :param tweet_idx: id твита
    :return: bool
    """

    try:
        tweet_id = await session.execute(
            select(Tweets.id).where(Tweets.id == tweet_idx)
        )
        if tweet_id.scalars().one_or_none():
            return True

    except Exception as err:
        logger.error(err)

    return False


async def check_follows_tweet_exists(
    session: AsyncSession, tweet_idx: int, user_idx: int
) -> bool:
    """
    проверка что твит есть, и он от пользователя на которого есть подписка
    :param session:
    :param tweet_idx: id твита
    :param user_idx: id пользователя
    :return: bool
    """

    try:
        query_followers = select(Followers.follower_id).where(
            Followers.user_id == user_idx
        )

        query_tweet = await session.scalar(
            select(Tweets.id).where(
                Tweets.user_id.in_(query_followers), Tweets.id == tweet_idx
            )
        )
        if query_tweet:
            return True
    except Exception as err:
        logger.error(err)

    return False


async def check_users_tweet_exists(
    session: AsyncSession, user_idx: int, tweet_idx: int
) -> bool:
    """
    проверка существования твита созданного заданным пользователем
    :param session:
    :param user_idx: id пользователя
    :param tweet_idx: id твита
    :return: bool
    """

    try:
        tweet_id = await session.execute(
            select(Tweets.id).where(Tweets.id == tweet_idx, Tweets.user_id == user_idx)
        )

        if tweet_id.scalars().one_or_none():
            return True

    except Exception as err:
        logger.error(err)

    return False


async def add_like_to_tweet(
    session: AsyncSession, user_idx: int, tweet_idx: int
) -> dict:
    """
    поставить лайк
    :param session:
    :param user_idx:
    :param tweet_idx:
    :return: dict результат операции
    """

    try:
        await session.execute(
            insert(Likes).values(user_id=user_idx, tweet_id=tweet_idx)
        )

        await update_user_last_activity(session, user_id=user_idx)
        await session.commit()

    except Exception as err:
        logger.error(err)
        return {"result": False}

    return {"result": True}


async def delete_like_to_tweet(
    session: AsyncSession, user_idx: int, tweet_idx: int
) -> dict:
    """
    удалить like, в таблице Likes удаляется строка
    :param session:
    :param user_idx:
    :param tweet_idx:
    :return: dict результат операции
    """

    try:
        result = await session.scalar(
            delete(Likes)
            .where(Likes.user_id == user_idx, Likes.tweet_id == tweet_idx)
            .returning(Likes.id)
        )

        await update_user_last_activity(session, user_id=user_idx)
        await session.commit()

        if result:
            return {"result": True}

    except Exception as err:
        logger.error(err)

    return {"result": False}


async def delete_tweet(session: AsyncSession, user_idx: int, tweet_idx: int) -> dict:
    """
    удалить tweet
    :param session:
    :param user_idx:
    :param tweet_idx:
    :return: dict результат операции
    """

    user = await check_user_exists(session, user_id=user_idx)
    if not user:
        err = f"User id={user_idx} not found."
        logger.error(err)
        return {"result": False, "error": err}

    tweet = await check_users_tweet_exists(session, user_idx, tweet_idx)
    if not tweet:
        err = f"Tweet id={tweet_idx} from user id={user_idx} not found."
        logger.error(err)
        return {"result": False, "error": err}

    result = await session.execute(
        delete(Tweets)
        .where(Tweets.user_id == user_idx, Tweets.id == tweet_idx)
        .returning(Tweets.id)
    )

    deleted_tweet_id = result.scalar()

    await update_user_last_activity(session, user_id=user_idx)
    await session.commit()

    res_delete_media = await delete_media(session, tweet_idx)

    if not res_delete_media:
        err = f"Deleted tweet id={tweet_idx} from user id={user_idx}, but error an deleting media files."
        logger.error(err)
        return {"result": False, "error": err}

    logger.info(f"Tweet id={tweet_idx} from user id={user_idx} was deleted successful.")
    return {"result": True}
