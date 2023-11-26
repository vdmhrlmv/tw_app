#!/bin/sh

alembic upgrade head

cd app_twitter/service || exit

gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:5000
