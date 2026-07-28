"""Captura IP real e user-agent do request atual em uma ContextVar, pra que
auditoria_service.registrar() grave essa informação em toda ação sem precisar
receber `Request` explicitamente em cada router/service (governança exige IP em
todo log de auditoria, não só no login)."""

from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_ip_atual: ContextVar[str | None] = ContextVar("_ip_atual", default=None)
_user_agent_atual: ContextVar[str | None] = ContextVar("_user_agent_atual", default=None)


def obter_ip_cliente(request: Request) -> str | None:
    """Atrás do nginx (proxy_set_header X-Real-IP $remote_addr), request.client.host
    é o IP do proxy, não do cliente real — por isso os headers têm prioridade."""
    if real_ip := request.headers.get("x-real-ip"):
        return real_ip
    if forwarded_for := request.headers.get("x-forwarded-for"):
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token_ip = _ip_atual.set(obter_ip_cliente(request))
        token_ua = _user_agent_atual.set(request.headers.get("user-agent"))
        try:
            return await call_next(request)
        finally:
            _ip_atual.reset(token_ip)
            _user_agent_atual.reset(token_ua)


def ip_atual() -> str | None:
    return _ip_atual.get()


def user_agent_atual() -> str | None:
    return _user_agent_atual.get()
