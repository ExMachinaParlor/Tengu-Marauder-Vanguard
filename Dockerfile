# Use a lightweight Python base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system and build dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libcap-dev \
    python3-opencv \
    udev \
    gcc \
    g++ \
    make \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    python3-picamera2 \
    libcamera-apps \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy files to container
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Default command to run Flask app
CMD ["python3", "Control/operatorcontroller.py"]
# Note: Ensure that the 'requirements.txt' file is present in the same directory as this Dockerfile.