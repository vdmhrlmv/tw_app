import gunicorn
from fastapi import FastAPI
from starlette.requests import Request
import uvicorn

from fastapi.staticfiles import StaticFiles

from models.database import engine
from routes import tweet_routes, user_routes
from logger.logger import logger
from tests.add_testdata_db import add_test_data_in_db

# todo  доделать README


app = FastAPI()
app.include_router(tweet_routes.router)
app.include_router(user_routes.router)

app.mount("/", StaticFiles(directory="static", html=True))


@app.middleware("http")
async def add_csp_header(request: Request, call_next):
    response = await call_next(request)
    # policy = "default-src *"
    # response.headers['Content-Security-Policy'] = policy
    return response


@app.on_event("startup")
async def startup():
    await add_test_data_in_db()
    logger.info(f'{__name__}:Engine begin')


@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()
    logger.info(f'{__name__}:Engine dispose')


@app.get('/')
async def root():
    return {"Name service": "Tweets"}


if __name__ == '__main__':
    logger.info(f'{__name__} App_twitter started...')
    # uvicorn.run(app, host="0.0.0.0", port=5000)
