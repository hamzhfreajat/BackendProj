FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg and dos2unix
RUN apt-get update && apt-get install -y gcc libpq-dev dos2unix && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Fix line endings and make the startup script executable
RUN dos2unix start_staging.sh && chmod +x start_staging.sh

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8081

CMD ["./start_staging.sh"]
