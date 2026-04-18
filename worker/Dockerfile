FROM python:3.11-slim

WORKDIR /worker

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /worker/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch torchvision && \
    pip install --no-cache-dir -r /worker/requirements.txt

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "technical_document_ml_service.workers.prediction_worker"]