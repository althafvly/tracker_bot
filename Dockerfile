FROM python:slim

WORKDIR /app

# Install system dependencies (git + ca-certificates for HTTPS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Configure a temp git identity
RUN git config --global user.name "TrackerBot" \
    && git config --global user.email "trackerbot@example.com"

# Copy only required files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY trackers/ ./trackers/
COPY config.py main.py notifier.py utils.py ./

# Default command
CMD ["python", "main.py"]
