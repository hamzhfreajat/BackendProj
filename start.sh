#!/bin/bash
# Start the ARQ worker in the background
arq worker.WorkerSettings &

# Start the FastAPI web server in the foreground with 4 workers to utilize all CPU cores
exec uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
