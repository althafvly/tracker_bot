FROM python:slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Default command: run every 15 minutes
CMD ["sh", "-c", "while true; do python tracker.py; sleep 900; done"]
