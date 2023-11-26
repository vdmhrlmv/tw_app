from datetime import datetime
from pathlib import Path
from os import remove, environ
from typing import Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete

from fastapi import UploadFile
from dotenv import load_dotenv

from logger.logger import logger
from models.models import Users, Followers, Tweets, Likes, Media


load_dotenv()

MEDIA_DIR = environ.get("MEDIA_DIR", "static/media")

FILES_DIR = Path(__file__).resolve().parent.parent.joinpath(MEDIA_DIR)


async def temp_file_name() -> str:
    """
    генерация имени файла для сохраннения на диске
    :return: имя файла
    """
    name = [s for s in str(datetime.now()) if s.isdigit()]
    return "".join(name) + ".tmp"


async def save_file(session: AsyncSession, file: UploadFile) -> Union[int, None]:
    """
    сохранение медиафайла на диск
    :param session: объект сессии
    :param file: объект - file прикрепленный к твиту
    :return: id загруженного файла
    """

    filename = await temp_file_name()

    try:
        with open(FILES_DIR.joinpath(filename), "wb") as f:
            f.write(file.file.read())
    except OSError as err:
        logger.error(f"Error {err} on save file:{filename}")
        return None

    try:
        result = await session.scalar(
            insert(Media)
            .values(
                filepath=filename,
            )
            .returning(Media.id)
        )
        await session.commit()
    except Exception as err:
        logger.error(err)
        return None

    return result


async def link_media_to_tweet(
    session: AsyncSession, media_id_list: tuple, tweet_id: int
):
    """
    привязывание загруженных медиа-файлов к твиту
    :param session: объект сессии
    :param media_id_list: список id медиа-файлов
    :param tweet_id: id твита
    :return:
    """

    try:
        await session.execute(
            update(Media)
            .values(
                tweet_id=tweet_id,
            )
            .where(Media.id.in_(media_id_list))
        )

        await session.commit()
    except Exception as err:
        logger.error(
            f"Media files id:{media_id_list} are not attached to tweet number:{tweet_id}. {err}"
        )


async def delete_files(files: list):
    """
    удаление файлов из каталога media
    :param files: список файлов удаляемого твита
    :return: результат операции
    """

    for filename in files:
        try:
            remove(FILES_DIR.joinpath(filename))
        except OSError as err:
            logger.error(f"Error on deleting file:{filename}. {err} ")
            return False
        else:
            logger.info(f"Deleted file {filename}")
    return True


async def delete_media(session: AsyncSession, tweet_idx: int) -> bool:
    """
    удаление из БД медиа-файлов прикрепленных к удаляемому твиту
    :param session: объект сессии
    :param media_id_list: список id медиа-файлов
    :param tweet_idx: id твита
    :return:
    """

    try:
        result = await session.scalars(
            delete(Media).where(Media.tweet_id == tweet_idx).returning(Media.filepath)
        )
        await session.commit()

        deleted_media_filepath = result.all()
    except Exception as err:
        logger.error(err)
        deleted_media_filepath = None

    if not deleted_media_filepath:
        logger.info(f"media for deleted tweet id={tweet_idx} not found")
        return True

    res = await delete_files(deleted_media_filepath)
    if not res:
        logger.error(f"Error when deleting files: {deleted_media_filepath}.")
        return False

    logger.info(f"Deleting media for tweet id={tweet_idx} completed successfully.")
    return True
