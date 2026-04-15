FROM python:3.11-slim

WORKDIR /worker

COPY requirements.txt /worker/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /worker/requirements.txt

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "technical_document_ml_service.workers.prediction_worker"]