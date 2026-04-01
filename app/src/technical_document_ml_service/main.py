from fastapi import FastAPI


app = FastAPI(
    title="Technical Document ML Service",
    description="Сервис извлечения и проверки данных из технической документации",
    version="0.1.0",
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Проверка работоспособности приложения"""
    return {"status": "ok"}