#!/bin/bash
# Start the ARQ worker in the background
arq worker.WorkerSettings &

# Start the FastAPI web server in the foreground with 4 workers to utilize all CPU cores
exec gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 --preload
