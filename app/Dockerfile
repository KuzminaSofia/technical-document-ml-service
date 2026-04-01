FROM python:3.11-slim

# рабочая директория внутри контейнера
WORKDIR /app

COPY requirements.txt /app/requirements.txt

# зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src

ENV PYTHONPATH=/app/src

# запустить
CMD ["uvicorn", "technical_document_ml_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
