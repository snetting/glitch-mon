FROM python:3.11-slim

WORKDIR /app

# Install dependencies and dictionary
RUN apt-get update && apt-get install -y wamerican && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure logs are visible in Docker/Podman
ENV PYTHONUNBUFFERED=1

# Copy the client script
COPY main.py .

# Run the monitor
CMD ["python", "main.py"]
