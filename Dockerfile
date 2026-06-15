FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make the startup script executable
RUN chmod +x start.sh

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8080

CMD ["./start.sh"]
