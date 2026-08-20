#!/bin/bash
# Start the FastAPI web server for STAGING on port 8081
exec uvicorn main:app --host 0.0.0.0 --port 8081 --workers 2
