from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import Response


WEB_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def render_template(
    request: Request,
    template_name: str,
    *,
    page_title: str,
    current_user: Any = None,
    status_code: int = 200,
    **context: Any,
) -> Response:
    """отрендерить HTML-шаблон с базовым контекстом"""
    template_context = {
        "request": request,
        "page_title": page_title,
        "current_user": current_user,
        **context,
    }
    return templates.TemplateResponse(
        template_name,
        template_context,
        status_code=status_code,
    )