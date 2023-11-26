# Димломный проект курса Python Advanced
сервис микроблогов а-ля Twitter

## Технологии
- [Python 3.10](https://www.python.org/downloads/release/python-3100/)
- [Pytest](https://docs.pytest.org/en/7.4.x/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/en/latest/)
- [Docker](https://www.docker.com/)


## Запуск Development сервера:
развернуть проект в отдельную директорию
установить виртуальное окружение - venv, установить зависимости:
```commandline
pip install requirements_dev.txt
```
настроить переменные окружения для разработки - в файле .env,
если установить ADD_TEST_DATA = "yes", то при старте приложения в базу данных будут добавлены тестовые данные

запустить БД
```commandline
docker-compose -f docker-compose-dev.yaml up --build
```
применить миграции 
```commandline
alembic upgrade head
```
перейти в каталог app_twitter/service/ и выполнить тесты
```commandline
pytest
```
запустить dev-сервер
```commandline
uvicorn main:app --reload --port 5000
```
приложение твиттера будет доступно по url:
```commandline
http://localhost:5000/
```
для просмотра документации и тестирования API:
```commandline
http://localhost:5000/docs
```


## Запуск Prod-сервера
Развернуть проект в отдельную директорию. Внести переменные окружения в файл .env.prod.
Выполнить сборку проекта командой
```commandline
docker-compose up --build
```
приложение твиттера будет доступно по url:
```commandline
http://localhost/
```
