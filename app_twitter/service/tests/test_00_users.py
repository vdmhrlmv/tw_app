import pytest
from httpx import AsyncClient

from main import app
from tests.conftest import engine_test, APIKEYS


LAST_ACTIVITY_TIME = None


@pytest.mark.anyio
async def test_root_00(prepare_database, init_test_data):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")

    assert response.status_code == 200

    await prepare_database
    await init_test_data


@pytest.mark.anyio
async def test_api_users_me_00():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/users/me", headers={"api-key": APIKEYS[2]})

    assert response.status_code == 200
    assert response.json()["user"]["id"] == 2
    assert response.json()["user"]["followers"] == [{"id": 3, "name": "User_name_3"}]
    assert response.json()["user"]["following"] == [{"id": 1, "name": "User_name_1"}]
    global LAST_ACTIVITY_TIME
    LAST_ACTIVITY_TIME = response.json()["user"]["last_activity"]


@pytest.mark.anyio
async def test_api_users_me_not_found():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/users/me", headers={"api-key": APIKEYS[0]})
    assert response.status_code == 404
    assert response.json()["result"] is False


async def test_api_get_user_by_id():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/users/1")
        assert response.status_code == 200
        assert response.json()["result"] is True
        assert response.json()["user"]["name"] == "User_name_1"

        response = await ac.get("/api/users/22")
        assert response.status_code == 404
        assert response.json()["result"] is False


async def test_api_follow_to_user():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # подписка на самого себя
        response = await ac.post("/api/users/3/follow", headers={"api-key": APIKEYS[3]})
        assert response.status_code == 404
        assert response.json()["result"] is False

        # успешная подписка
        response = await ac.post("/api/users/1/follow", headers={"api-key": APIKEYS[3]})
        assert response.status_code == 201
        assert response.json()["result"] is True

        response = await ac.get("/api/users/3")
        assert response.status_code == 200
        assert response.json()["user"]["following"] == [
            {"id": 2, "name": "User_name_1"},
            {"id": 3, "name": "User_name_2"},
        ]
        assert response.json()["user"]["followers"] == [
            {"id": 4, "name": "User_name_1"}
        ]

        # повторная подписка на того же пользователя
        response = await ac.post("/api/users/3/follow", headers={"api-key": APIKEYS[1]})
        assert response.status_code == 404
        assert response.json()["result"] is False


async def test_api_delete_follow_to_user():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # удаление несуществующей подписки
        response = await ac.delete(
            "/api/users/1/follow", headers={"api-key": APIKEYS[2]}
        )
        assert response.status_code == 404
        assert response.json()["result"] is False

        response = await ac.delete(
            "/api/users/2/follow", headers={"api-key": APIKEYS[1]}
        )
        assert response.status_code == 200
        assert response.json()["result"] is True

        response = await ac.get("/api/users/2")
        assert response.status_code == 200
        assert response.json()["result"] is True
        assert response.json()["user"]["following"] == []
        assert response.json()["user"]["followers"] == [
            {"id": 3, "name": "User_name_3"}
        ]

        # проверка изменения времени последней активности
        response = await ac.delete(
            "/api/users/3/follow", headers={"api-key": APIKEYS[2]}
        )
        assert response.status_code == 200
        assert response.json()["result"] is True

        response = await ac.get("/api/users/2")
        assert response.status_code == 200
        assert response.json()["result"] is True
        assert response.json()["user"]["last_activity"] != LAST_ACTIVITY_TIME
