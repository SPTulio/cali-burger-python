"""Exceções de domínio e conversão para respostas HTTP padronizadas.

Todas as respostas de erro têm o formato:
    {"error": {"code": "...", "message": "...", "fields": {"campo": "mensagem"}}}
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("caliburger.errors")


class AppError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"

    def __init__(
        self, message: str, *, code: str | None = None, fields: dict[str, str] | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.fields = fields or {}


class InvalidInput(AppError):
    """Entrada inválida que só pode ser verificada com o banco (ex.: usuário já existe)."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "validation_error"


class BusinessRuleError(AppError):
    """A operação viola uma regra de negócio no estado atual (ex.: estoque insuficiente)."""

    status_code = status.HTTP_409_CONFLICT
    code = "business_rule"


class NotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class Unauthorized(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class Forbidden(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


class RateLimited(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"

    def __init__(self, message: str, *, retry_after: int) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def error_body(code: str, message: str, fields: dict[str, str] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "fields": fields or {}}}


# Mensagens do Pydantic traduzidas para o usuário final.
_PYDANTIC_MESSAGES: dict[str, str] = {
    "missing": "Campo obrigatório.",
    "string_too_short": "Use pelo menos {min_length} caractere(s).",
    "string_too_long": "Use no máximo {max_length} caracteres.",
    "string_type": "Informe um texto.",
    "int_parsing": "Informe um número inteiro.",
    "int_type": "Informe um número inteiro.",
    "int_from_float": "Informe um número inteiro.",
    "decimal_parsing": "Informe um número válido.",
    "decimal_max_places": "Use no máximo {decimal_places} casas decimais.",
    "greater_than": "O valor deve ser maior que {gt}.",
    "greater_than_equal": "O valor deve ser no mínimo {ge}.",
    "less_than": "O valor deve ser menor que {lt}.",
    "less_than_equal": "O valor deve ser no máximo {le}.",
    "date_from_datetime_parsing": "Informe uma data válida.",
    "date_parsing": "Informe uma data válida.",
    "date_type": "Informe uma data válida.",
    "enum": "Opção inválida.",
    "literal_error": "Opção inválida.",
    "too_short": "Informe pelo menos {min_length} item(ns).",
    "too_long": "Informe no máximo {max_length} itens.",
    "string_pattern_mismatch": "Formato inválido.",
    "json_invalid": "JSON inválido.",
    "model_attributes_type": "Formato inválido.",
}


def _translate(error: dict[str, Any]) -> str:
    if error["type"] == "value_error":
        # Mensagens próprias dos validadores (ex.: "CPF inválido.").
        return str(error.get("ctx", {}).get("error", error["msg"]))
    if error["type"] == "value_error.email" or "email" in error["msg"].lower():
        return "E-mail inválido."
    template = _PYDANTIC_MESSAGES.get(error["type"])
    if template is None:
        return "Valor inválido."
    try:
        return template.format(**error.get("ctx", {}))
    except KeyError:
        return template


def _field_name(loc: tuple[Any, ...]) -> str:
    parts = [str(p) for p in loc if p not in ("body", "query", "path", "header")]
    return ".".join(parts) or "__root__"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        headers = {}
        if isinstance(exc, RateLimited):
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(
            error_body(exc.code, exc.message, exc.fields),
            status_code=exc.status_code,
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields: dict[str, str] = {}
        for err in exc.errors():
            fields.setdefault(_field_name(tuple(err["loc"])), _translate(err))
        return JSONResponse(
            error_body("validation_error", "Revise os campos destacados.", fields),
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        messages = {
            404: "Recurso não encontrado.",
            405: "Método não permitido.",
            413: "Arquivo muito grande.",
        }
        message = messages.get(exc.status_code, str(exc.detail))
        return JSONResponse(
            error_body("http_error", message),
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Erro inesperado em %s %s", request.method, request.url.path)
        return JSONResponse(
            error_body("internal_error", "Ocorreu um erro inesperado. Tente novamente."),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
