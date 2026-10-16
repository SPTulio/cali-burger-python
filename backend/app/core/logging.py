"""Logs com identificador de requisição. Nunca registra corpo de requisição, senhas ou tokens."""

import logging
import time
import uuid
from contextvars import ContextVar

from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s")
    )
    handler.addFilter(_RequestIdFilter())
    root = logging.getLogger("caliburger")
    root.handlers = [handler]
    root.setLevel(level.upper())
    root.propagate = False


class RequestContextMiddleware:
    """Gera um id por requisição, registra método/rota/status/duração e aplica
    cabeçalhos de segurança em todas as respostas."""

    SECURITY_HEADERS = (
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"referrer-policy", b"same-origin"),
        (b"cross-origin-opener-policy", b"same-origin"),
    )

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.logger = logging.getLogger("caliburger.http")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex[:12]
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                existing = {k.lower() for k, _ in headers}
                headers.extend(h for h in self.SECURITY_HEADERS if h[0] not in existing)
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = (time.perf_counter() - started) * 1000
            self.logger.info(
                "%s %s -> %s (%.1f ms)", scope["method"], scope["path"], status_code, elapsed
            )
            request_id_var.reset(token)
