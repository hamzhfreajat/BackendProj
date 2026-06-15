#!/bin/bash
# Start the ARQ worker in the background
arq worker.WorkerSettings &

# Start the FastAPI web server in the foreground
exec uvicorn main:app --host 0.0.0.0 --port 8080
