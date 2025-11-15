# -------------------------------
# Base image: lightweight Python 3.12
# -------------------------------
FROM python:3.12-slim

# -------------------------------
# Environment variables
# -------------------------------
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# -------------------------------
# Pre-clean and install dependencies
# -------------------------------
# The cleanup before installation ensures minimal layer size
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && apt-get update && apt-get install -y --no-install-recommends \
       chromium chromium-driver \
       curl wget unzip gnupg ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# -------------------------------
# Environment variables for Selenium
# -------------------------------
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# -------------------------------
# Set working directory
# -------------------------------
WORKDIR /app

# -------------------------------
# Copy Python dependencies
# -------------------------------
COPY requirements.txt .

# -------------------------------
# Install Python packages (pytest, selenium, etc.)
# -------------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------
# Copy application code
# -------------------------------
COPY . .

# -------------------------------
# Default command
# -------------------------------
# Keeps container alive for Jenkins tests
CMD ["python", "app.py"]

