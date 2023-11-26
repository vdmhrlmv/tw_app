from typing import Union

from fastapi import APIRouter, Header
from fastapi import Depends
from starlette import status
from starlette.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from utils.users import (
    get_user_by_apikey,
    get_user_by_id,
    follow_to_user,
    delete_follower_to_user,
)
from models.database import get_async_session


router = APIRouter()


@router.get("/api/users/me")
async def get_my_profile(
    api_key: Union[str, None] = Header(default=None),
    session: AsyncSession = Depends(get_async_session),
):
    """
    9.возвращает профиль пользователя
    :return:
    """

    result = await get_user_by_apikey(session, api_key)
    if result["result"]:
        return JSONResponse(content=result, status_code=status.HTTP_200_OK)
    return JSONResponse(content=result, status_code=status.HTTP_404_NOT_FOUND)


@router.get("/api/users/{idx}")
async def get_my_profile(idx: int, session: AsyncSession = Depends(get_async_session)):
    """
    10.возвращает профиль пользователя по user_id
    :param idx: user_id
    :param session:
    :return: словарь с результатом операции и объектом пользователя
    """

    user = await get_user_by_id(session, idx)

    if user["result"]:
        return JSONResponse(content=user, status_code=status.HTTP_200_OK)
    return JSONResponse(content=user, status_code=status.HTTP_404_NOT_FOUND)


@router.post("/api/users/{idx}/follow")
async def add_follower_to_user(
    idx: int,
    api_key: Union[str, None] = Header(default=None),
    session: AsyncSession = Depends(get_async_session),
):
    """
    6.добавление подписки на пользователя
    :param idx:
    :param api_key:
    :param session:
    :return:
    """

    add_follower = await follow_to_user(session, api_key, idx)

    if add_follower["result"]:
        return JSONResponse(content=add_follower, status_code=status.HTTP_201_CREATED)
    return JSONResponse(content=add_follower, status_code=status.HTTP_404_NOT_FOUND)


@router.delete("/api/users/{idx}/follow")
async def del_follower_to_user(
    idx: int,
    api_key: Union[str, None] = Header(default=None),
    session: AsyncSession = Depends(get_async_session),
):
    """
    7.удаление подписки на пользователя
    :param idx:
    :param api_key:
    :param session:
    :return:
    """

    delete_follower = await delete_follower_to_user(session, api_key, idx)

    if delete_follower["result"]:
        return JSONResponse(content=delete_follower, status_code=status.HTTP_200_OK)
    return JSONResponse(content=delete_follower, status_code=status.HTTP_404_NOT_FOUND)
