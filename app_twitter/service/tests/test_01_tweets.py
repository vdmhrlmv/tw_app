import pytest
from httpx import AsyncClient

from main import app
from .conftest import APIKEYS, TWEETS


async def test_api_add_tweet():
    # создание твита
    async with AsyncClient(app=app, base_url="http://test") as ac:
        tweet_data = {"tweet_data": "Test tweet from User_0.", "tweet_media_ids": (0,)}

        response = await ac.post(
            "/api/tweets", headers={"api-key": APIKEYS[1]}, json=tweet_data
        )
        assert response.status_code == 201
        assert response.json()["result"] is True
        TWEETS[1].append(response.json()["tweet_id"])

        response = await ac.post(
            "/api/tweets",
            headers={"api-key": APIKEYS[1]},
            json={
                "tweet_data": "Test tweet number two from User_1.",
                "tweet_media_ids": (0,),
            },
        )
        assert response.status_code == 201
        assert response.json()["result"] is True
        TWEETS[1].append(response.json()["tweet_id"])

        response = await ac.post(
            "/api/tweets",
            headers={"api-key": APIKEYS[2]},
            json={"tweet_data": "Test tweet from User_2.", "tweet_media_ids": (0,)},
        )
        assert response.json()["result"] is True
        TWEETS[2].append(response.json()["tweet_id"])

        response = await ac.post(
            "/api/tweets",
            headers={"api-key": APIKEYS[3]},
            json={"tweet_data": "Test tweet from User_3.", "tweet_media_ids": (0,)},
        )
        assert response.json()["result"] is True
        TWEETS[3].append(response.json()["tweet_id"])


async def test_api_add_like():
    # поставить like
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            f"/api/tweets/{TWEETS[3][0]}/likes", headers={"api-key": APIKEYS[1]}
        )
        assert response.status_code == 201
        assert response.json()["result"] is True

        # like на несуществующий твит
        response = await ac.post(
            "/api/tweets/5555/likes", headers={"api-key": APIKEYS[1]}
        )
        assert response.status_code == 404
        assert response.json()["result"] is False

        # like от несуществующего пользователя
        response = await ac.post(
            f"/api/tweets/{TWEETS[1][0]}/likes", headers={"api-key": APIKEYS[0]}
        )
        assert response.status_code == 403
        assert response.json()["result"] is False

        # like на твит от неподписанного пользователя
        response = await ac.post(
            f"/api/tweets/{TWEETS[1][0]}/likes", headers={"api-key": APIKEYS[2]}
        )
        assert response.status_code == 404
        assert response.json()["result"] is False


async def test_api_get_tweet_list():
    # получение ленты твитов 3-го юзера
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/tweets", headers={"api-key": APIKEYS[3]})
        assert response.status_code == 200
        assert response.json()["result"] is True


async def test_api_delete_like():
    # удаление лайка
    # лайк ставит User2 на 1-ый твит от User3
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            f"/api/tweets/{TWEETS[3][0]}/likes", headers={"api-key": APIKEYS[1]}
        )
        assert response.status_code == 201
        assert response.json()["result"] is True
        # удаление лайка
        response = await ac.delete(
            f"/api/tweets/{TWEETS[3][0]}/likes", headers={"api-key": APIKEYS[1]}
        )
        assert response.status_code == 200
        assert response.json()["result"] is True
        # удаление несуществующего лайка
        response = await ac.delete(
            f"/api/tweets/{TWEETS[3][0]}/likes", headers={"api-key": APIKEYS[1]}
        )
        assert response.status_code == 404
        assert response.json()["result"] is False


async def test_api_delete_tweet():
    # удаление твита
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # создание твит от User_1
        tweet_data = {
            "tweet_data": "Test tweet for delete from User_1.",
            "tweet_media_ids": (0,),
        }

        response = await ac.post(
            "/api/tweets", headers={"api-key": APIKEYS[1]}, json=tweet_data
        )
        assert response.status_code == 201
        assert response.json()["result"] is True
        deleted_tweet_id = response.json()["tweet_id"]

        # удаление созданного твита
        response = await ac.delete(
            f"/api/tweets/{deleted_tweet_id}", headers={"api-key": APIKEYS[1]}
        )
        assert response.status_code == 200
        assert response.json()["result"] is True

        # получение ленты твитов для проверки что твит удален
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/api/tweets", headers={"api-key": APIKEYS[1]})
            assert response.status_code == 200
            assert response.json()["result"] is True
            result = True
            for tweet in response.json()["tweets"]:
                if tweet["id"] == deleted_tweet_id:
                    result = False
                    break
            assert result is True


@pytest.mark.anyio
async def test_tweet_with_media():
    test_file = "tests/test_upload_file.jpg"

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/medias",
            headers={"api-key": APIKEYS[1]},
            files={"file": (test_file, open(test_file, "rb"))},
        )

        assert response.status_code == 201

        media_id = response.json()["media_id"]

        tweet_data = {
            "tweet_data": "Test tweet from User_1.",
            "tweet_media_ids": (media_id,),
        }
        response = await ac.post(
            "/api/tweets", headers={"api-key": APIKEYS[1]}, json=tweet_data
        )

        assert response.status_code == 201

        new_tweet_id = response.json()["tweet_id"]

        # удаление твита с картинкой
        response = await ac.delete(
            f"/api/tweets/{new_tweet_id}", headers={"api-key": APIKEYS[1]}
        )

        assert response.status_code == 200
