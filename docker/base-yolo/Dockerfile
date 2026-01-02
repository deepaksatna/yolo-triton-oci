FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    torch==2.1.0 \
    torchvision==0.16.0 \
    ultralytics==8.0.196 \
    opencv-python-headless==4.8.1.78 \
    numpy==1.24.3 \
    pillow==10.1.0

# Copy server code
COPY server.py /app/server.py

# Download YOLOv8s model (will be downloaded on first run)
# Model will be cached in /root/.config/Ultralytics/

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run Flask server
CMD ["python", "server.py"]
