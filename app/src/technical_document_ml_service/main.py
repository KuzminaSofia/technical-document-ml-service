from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from technical_document_ml_service.db.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Technical Document ML Service",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}