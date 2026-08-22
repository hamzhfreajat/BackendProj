#!/bin/bash
set -e
# Run database migrations
alembic upgrade head

# Start the FastAPI web server for STAGING on port 8081
exec gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8081 --preload
