# Technical Document ML Service

## Тема проекта

**Сервис извлечения и проверки данных из технической документации**

Пользователь загружает технические документы (PDF или изображения), ML-сервис извлекает из них структурированные данные, проводит валидацию входных данных и возвращает результат обработки. 

## реализовано в рамках задания №1

---

## Что реализовано на текущем этапе

### Задание №1 — объектная модель ML-сервиса

В проекте спроектирована доменная объектная модель, которая отражает базовую бизнес-логику сервиса

Реализованы основные сущности предметной области:

- `User` — пользователь сервиса;
- `MLModel` — базовая ML-модель;
- `TechnicalDocumentExtractionModel` — ML-модель для обработки технической документации;
- `MLTask` — базовая ML-задача;
- `DocumentExtractionTask` — задача на обработку документов;
- `PredictionResult` — результат работы модели;
- `MLRequestHistoryRecord` — история запросов;
- `Transaction` — базовая транзакция;
- `CreditTransaction` — пополнение баланса;
- `DebitTransaction` — списание средств;
- `UploadedDocument` — загруженный документ;
- `ValidationIssue` — ошибка валидации входных данных.

### Задание №2 — структура проекта и Docker Compose

Проект приведен к воспроизводимой инфраструктурной структуре и подготовлен к запуску через Docker Compose

Описаны 4 сервиса:

- `app` — backend-приложение;
- `web-proxy` — reverse proxy на Nginx;
- `rabbitmq` — брокер сообщений;
- `database` — база данных PostgreSQL

---

## Текущая структура проекта

```text
technical-document-ml-service/
├── app/
│   ├── .env
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       └── technical_document_ml_service/
│           ├── __init__.py
│           ├── main.py
│           └── domain/
│               ├── __init__.py
│               ├── entities.py
│               ├── enums.py
│               └── exceptions.py
├── web-proxy/
│   ├── Dockerfile
│   └── nginx.conf
├── storage/
│   ├── postgres/
│   └── rabbitmq/
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── .gitignore