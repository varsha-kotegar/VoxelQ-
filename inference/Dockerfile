FROM python:3.11-slim

# opencv-python needs these system libs even in headless environments
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only PyTorch and torchvision (much smaller download size ~150MB total)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download YOLOv8n weights at build time so the container doesn't need
# internet access on every startup / first job.
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]