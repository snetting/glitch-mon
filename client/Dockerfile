FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the client script
COPY main.py .

# Run the monitor
CMD ["python", "main.py"]
