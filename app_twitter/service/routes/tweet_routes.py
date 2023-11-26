from typing import Union

from fastapi import APIRouter, Header, UploadFile
from fastapi import Depends
from starlette import status
from starlette.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from utils.users import get_user_by_apikey, check_user_exists
from utils.tweets import (
    add_tweet,
    tweets_list,
    check_tweet_exists,
    add_like_to_tweet,
    delete_like_to_tweet,
    delete_tweet,
    check_users_tweet_exists,
    check_follows_tweet_exists,
)
from utils.media import save_file

from logger.logger import logger
from models.database import get_async_session
from schemas.schemas import BaseTweet


router = APIRouter()


@router.post("/api/tweets")
async def add_tweet_route(
    tweet_data: BaseTweet,
    api_key: Union[str, None] = Header(default=None),
    session: AsyncSession = Depends(get_async_session),
):
    """
    1.создание твита
    :param tweet_data: содержание твита
    :param api_key: ключ авторизации пользователя
    :param session: экземпляр сессии для работы с БД
    :return: json-объект с результатом операции, id - созданного твита
    """

    user = await get_user_by_apikey(session, api_key)

    if not user:
        logger.error(f"User not found.")
        return JSONResponse(
            content={
                "result": False,
                "error_type": "Authorisation Error.",
                "error_message": "Invalid authorization key.",
            },
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if user:
        tweet_id = await add_tweet(
            session,
            user["user"]["id"],
            tweet_data.tweet_data,
            tweet_data.tweet_media_ids,
        )
        if tweet_id:
            return JSONResponse(
                content={"result": True, "tweet_id": tweet_id},
                status_code=status.HTTP_201_CREATED,
            )
        return JSONResponse(
            content={"result": False}, status_code=status.HTTP_403_FORBIDDEN
        )

    logger.info(f"Wrong api-key: {api_key}.")
    return JSONResponse(
        content={
            "result": False,
            "error_type": "Authorisation Error.",
            "error_message": "Invalid authorization key.",
        },
        status_code=status.HTTP_403_FORBIDDEN,
    )


@router.get("/api/tweets")
async def get_tweets_list(
    api_key: Union[str, None] = Header(default=None),
    session: AsyncSession = Depends(get_async_session),
):
    """
    8. получить ленту с твитами
    :param api_key: ключ авторизации пользователя
    :param session: экземпляр сессии работы с БД
    :return:
    """

    user = await check_user_exists(session, apikey=api_key)
    if user:
        result = await tweets_list(session, user["id"])
        return JSONResponse(
            content={"result": True, "tweets": result}, status_code=status.HTTP_200_OK
        )

    return JSONResponse(
        content={
            "result": False,
            "error_type": "Authorisation Error.",
            "error_message": "Invalid authorization key.",
        },
        status_code=status.HTTP_403_FORBIDDEN,
    )


@router.post("/api/tweets/{idx}/likes")
async def add_like(
    idx: int,
    api_key: Union[str, None] = Header(default=None),
    session: AsyncSession = Depends(get_async_session),
):
    """
    4.поставить like
    :param idx: id твита
    :param api_key: ключ авторизации пользователя
    :param session: экземпляр сессии работы с БД
    :return: результат операции
    """

    user = await check_user_exists(session, apikey=api_key)

    if not user:
        return JSONResponse(
            content={
                "result": False,
                "error_type": "Authorisation Error.",
                "error_message": "Invalid authorization key.",
            },
            status_code=status.HTTP_403_FORBIDDEN,
        )

    tweet = await check_follows_tweet_exists(session, idx, user["id"])

    if tweet:
        result = await add_like_to_tweet(session, user["id"], idx)

        return JSONResponse(content=result, status_code=status.HTTP_201_CREATED)

    return JSONResponse(
        content={
            "result": False,
            "error_type": "tweet not found",
            "error_message": "tweet from following users not found",
        },
        status_code=status.HTTP_404_NOT_FOUND,
    )


@router.delete("/api/tweets/{idx}/likes")
async def del_like(
    idx: int,
    api_key: Union[str, None] = Header(default=None),
    session: AsyncSession = Depends(get_async_session),
):
    """
    5.убрать отметку нравится с твита
    :param idx: id лайка
    :param api_key: ключ авторизации пользователя
    :param session: экземпляр сессии работы с БД
    :return: результат операции
    """

    user = await check_user_exists(session, apikey=api_key)

    if not user:
        return JSONResponse(
            content={
                "result": False,
                "error_type": "Authorisation Error.",
                "error_message": "Invalid authorization key.",
            },
            status_code=status.HTTP_403_FORBIDDEN,
        )

    tweet = await check_follows_tweet_exists(session, idx, user["id"])

    if tweet:
        result = await delete_like_to_tweet(session, user["id"], idx)
        if result["result"]:
            return JSONResponse(
                content={"result": True}, status_code=status.HTTP_200_OK
            )

    return JSONResponse(
        content={
            "result": False,
            "error_type": "tweet or user not found",
            "error_message": "tweet or user not found",
        },
        status_code=status.HTTP_404_NOT_FOUND,
    )


@router.delete("/api/tweets/{idx}")
async def del_tweet(
    idx: int,
    api_key: Union[str, None] = Header(default=None),
    session: AsyncSession = Depends(get_async_session),
):
    """
    3. удаление твита
    :param idx: id твита
    :param api_key: ключ авторизации пользователя
    :param session: экземпляр сессии работы с БД
    :return: результат операции
    """

    user = await check_user_exists(session, apikey=api_key)
    if not user:
        logger.error(f"User not found.")
        return JSONResponse(
            content={
                "result": False,
                "error_type": "Authorisation Error.",
                "error_message": "Invalid authorization key.",
            },
            status_code=status.HTTP_403_FORBIDDEN,
        )

    tweet = await check_users_tweet_exists(session, user["id"], idx)
    if tweet:
        result = await delete_tweet(session, user["id"], idx)

        if result["result"]:
            return JSONResponse(
                content={"result": True}, status_code=status.HTTP_200_OK
            )

    logger.error(f"tweet id={idx} from user id={user['id']} not found")
    return JSONResponse(
        content={
            "result": False,
            "error_type": "tweet not found",
            "error_message": f"tweet id={idx} from user id={user['id']} not found",
        },
        status_code=status.HTTP_404_NOT_FOUND,
    )


@router.post("/api/medias")
async def upload_media(
    file: UploadFile, session: AsyncSession = Depends(get_async_session)
):
    """
    2. загрузка файлов из твита
    :param file:    объект файла
    :param session: сессия для работы с БД
    :return:        возвращает id медиа файла
    """

    result = await save_file(session, file)

    if result:
        return JSONResponse(
            content={"result": True, "media_id": result},
            status_code=status.HTTP_201_CREATED,
        )

    return JSONResponse(
        content={"result": False}, status_code=status.HTTP_404_NOT_FOUND
    )
