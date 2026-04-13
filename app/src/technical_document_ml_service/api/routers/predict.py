from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from technical_document_ml_service.api.deps import CurrentUserDep, SessionDep
from technical_document_ml_service.api.schemas.predict import PredictResponse
from technical_document_ml_service.services.document_storage_service import (
    IncomingDocumentData,
)
from technical_document_ml_service.services.prediction_service import (
    execute_document_prediction,
)


router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("", response_model=PredictResponse)
def predict_documents(
    session: SessionDep,
    current_user: CurrentUserDep,
    model_name: Annotated[str, Form(min_length=1)],
    target_schema: Annotated[str, Form(min_length=1)],
    documents: Annotated[list[UploadFile], File(...)],
) -> PredictResponse:
    """отправить документы на ML-обработку"""
    incoming_documents: list[IncomingDocumentData] = []

    try:
        for document in documents:
            content = document.file.read()
            incoming_documents.append(
                IncomingDocumentData(
                    filename=document.filename or "document",
                    content_type=document.content_type,
                    content=content,
                )
            )
    finally:
        for document in documents:
            document.file.close()

    execution = execute_document_prediction(
        session,
        user_id=current_user.id,
        model_name=model_name,
        target_schema=target_schema,
        documents=incoming_documents,
    )

    return PredictResponse.from_execution(execution)