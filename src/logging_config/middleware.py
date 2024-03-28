import time

import structlog

from asgi_correlation_id.context import correlation_id
from fastapi import Request
from starlette.types import ASGIApp, Scope, Receive, Send, Message


class LoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        info: Message = {}

        async def inner_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                info["response"] = message

            await send(message)

        request = Request(scope)

        structlog.contextvars.clear_contextvars()
        request_id = correlation_id.get() or ""
        url = request.url
        client_host = request.client.host if request.client else ""
        client_port = request.client.port if request.client else ""

        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            url=url,
            network={"client": {"ip": client_host, "port": client_port}},
        )

        logger: structlog.stdlib.BoundLogger = structlog.get_logger()
        start_time = time.perf_counter_ns()

        try:
            await self.app(scope, receive, inner_send)
        except Exception:
            logger.exception("Uncaught exception")
            info["response"]["status"] = 500
            raise
        finally:
            process_time = time.perf_counter_ns() - start_time
            status_code: int = info["response"]["status"]
            http_method = request.method
            http_version = request.scope["http_version"]
            await logger.ainfo(
                f'{client_host}:{client_port} - "{http_method} {url} HTTP/{http_version}" {status_code}',
                http={
                    "url": str(url),
                    "status_code": status_code,
                    "method": http_method,
                    "request_id": request_id,
                    "version": http_version,
                },
                duration=process_time,
                tag="request",
            )
