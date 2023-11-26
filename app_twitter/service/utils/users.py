import datetime
from typing import Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete

from logger.logger import logger
from models.models import Users, Followers


async def check_user_exists(
    session: AsyncSession, user_id: int = None, apikey: str = None
) -> Union[dict, None]:
    """
    проверка существования пользователя
    :param session:
    :param user_id: если параметр задан то проверка по id
    :param apikey: если параметр задан, и не задан user_id, то проверка по apikey
    :return: объект User
    """

    try:
        if user_id:
            result = await session.execute(select(Users).filter(Users.id == user_id))
            user_obj = result.scalars().one_or_none()
            if user_obj:
                return user_obj.to_json()
        elif apikey:
            result = await session.execute(select(Users).filter(Users.apikey == apikey))
            user_obj = result.scalars().one_or_none()
            if user_obj:
                return user_obj.to_json()
    except Exception as err:
        logger.error(err)

    return None


async def update_user_last_activity(session: AsyncSession, user_id: int) -> bool:
    """
    обновление времени последней активности пользователя
    :param session:
    :param user_id: id пользователя
    :return: результат операции
    """

    try:
        result = await session.scalar(
            update(Users)
            .where(Users.id == user_id)
            .values(last_activity=datetime.datetime.now())
            .returning(Users.id)
        )
        await session.commit()
        if result:
            return True
    except Exception as err:
        logger.error(err)
    logger.error("User not found for updating last activity time.")
    return False


async def get_user_by_apikey(session: AsyncSession, apikey: str) -> Users:
    """
    возвращет профиль пользователя по api-key
    :param session: AsyncSession
    :param apikey: str
    :return: User
    """

    try:
        user_obj = await session.scalar(select(Users).filter(Users.apikey == apikey))

        if user_obj:
            result = {"result": True, "user": user_obj.to_json()}

            followers = await get_followers_by_user_id(
                session, int(result["user"]["id"])
            )
            following = await get_following_by_user_id(
                session, int(result["user"]["id"])
            )

            result["user"]["followers"] = followers
            result["user"]["following"] = following

        else:
            result = {
                "result": False,
                "error_type": "User not found",
                "error_message": f"User with APIKEY={apikey} was not found",
            }

        return result

    except Exception as err:
        logger.error(err)
        return {
            "result": False,
            "error_type": "DB error",
            "error_message": "Error when accessing the database.",
        }


async def get_user_by_id(session: AsyncSession, idx: str) -> Users:
    """
    возвращет профиль пользователя по user_id
    :param session: AsyncSession
    :param idx: str
    :return: User
    """

    try:
        user_obj = await session.scalar(select(Users).filter(Users.id == int(idx)))

        if user_obj:
            result = {"result": True, "user": user_obj.to_json()}

            followers = await get_followers_by_user_id(
                session, int(result["user"]["id"])
            )
            following = await get_following_by_user_id(
                session, int(result["user"]["id"])
            )

            result["user"]["followers"] = followers
            result["user"]["following"] = following

        else:
            result = {
                "result": False,
                "error_type": "User not found",
                "error_message": f"User with ID={idx} was not found",
            }

        return result
    except Exception as err:
        logger.error(err)
        return {
            "result": False,
            "error_type": "DB error",
            "error_message": "Error when accessing the database.",
        }


async def get_followers_by_user_id(session: AsyncSession, user_idx: int) -> list:
    """
    возвращет список подписанных на пользователя
    :param session: AsyncSession
    :param user_id: int
    :return: list
    """

    try:
        followers = await session.scalars(
            select(Followers).filter(Followers.user_id == user_idx)
        )
        result = list()
        for obj in followers:
            user_name = await session.scalar(
                select(Users.name).filter(Users.id == obj.follower_id)
            )

            result.append({"id": obj.id, "name": user_name})

        return result
    except Exception as err:
        logger.error(err)
        return []


async def get_following_by_user_id(session: AsyncSession, user_id: int) -> list:
    """
    возвращет список на кого подписан пользователь
    :param session: AsyncSession
    :param user_id: int
    :return: list
    """

    try:
        following = await session.execute(
            select(Followers).filter(Followers.follower_id == user_id)
        )
        return [{"id": obj.id, "name": obj.user.name} for obj in following.scalars()]
    except Exception as err:
        logger.error(err)
        return []


async def follow_to_user(session: AsyncSession, apikey: str, user_idx: int) -> dict:
    """
    выполняет добавление фолловера пользователю
    :param session:
    :param apikey: ключ аутентификации пользователя от имени которого выполняется подписка
    :param user_idx: идентификатор пользователя на которого подписываются
    :return: возвращает результат операции
    """

    check_user_apikey = await check_user_exists(session, apikey=apikey)
    check_user_id = await check_user_exists(session, user_id=user_idx)

    # проверка что такие пользователи существуют и юзер и фалловер не один и тот же пользователь
    if (
        check_user_apikey
        and check_user_id
        and check_user_apikey["id"] != check_user_id["id"]
    ):
        try:
            check_followers = await session.execute(
                select(Followers).filter(
                    Followers.user_id == check_user_apikey["id"],
                    Followers.follower_id == user_idx,
                )
            )
        except Exception as err:
            logger.error(err)
            return {"result": False}

        # если такой пары фалловер-юзер не существует, то добавляем фалловера
        if not check_followers.scalars().one_or_none():
            try:
                await session.execute(
                    insert(Followers).values(
                        follower_id=user_idx, user_id=check_user_apikey["id"]
                    )
                )
                await session.commit()

                await update_user_last_activity(
                    session, user_id=check_user_apikey["id"]
                )

            except Exception as err:
                logger.error(err)
                return {"result": False}
            return {"result": True}
        logger.info(
            f"Add follower error. Follower:{check_user_apikey['name']} to user:{check_user_id['name']} "
            f"already exists."
        )
        return {"result": False}
    logger.info(
        f"Add follower error. User:{user_idx} or " f"follower:{apikey} does not exists."
    )
    return {"result": False}


async def delete_follower_to_user(
    session: AsyncSession, apikey: str, user_idx: int
) -> dict:
    """
    удаление подписки на пользователя
    :param session:
    :param apikey: ключ аутентификации пользователя от имени которого удаляется подписка
    :param user_idx: идентификатор пользователя подписка на которого удаляется
    :return: возвращает результат операции
    """

    check_user_apikey = await check_user_exists(session, apikey=apikey)

    try:
        # проверка на существование такого фалловера
        check_followers = await session.execute(
            select(Followers).filter(
                Followers.user_id == check_user_apikey["id"],
                Followers.follower_id == user_idx,
            )
        )

        if check_followers.scalars().one_or_none():
            # фалловер существует - удаляем его

            await session.execute(
                delete(Followers).where(
                    Followers.user_id == check_user_apikey["id"],
                    Followers.follower_id == user_idx,
                )
            )

            await session.commit()

            await update_user_last_activity(session, user_id=check_user_apikey["id"])
            return {"result": True}

    except Exception as err:
        logger.error(err)

    logger.info(
        f"Delete follower error. User:{user_idx} with "
        f"follower:{apikey} does not exists."
    )

    return {"result": False}
