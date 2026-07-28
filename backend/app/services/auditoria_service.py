from sqlalchemy.orm import Session

from app.middleware.request_context import ip_atual, user_agent_atual
from app.models.enums import AcaoAuditoria
from app.models.log_auditoria import LogAuditoria


def registrar(
    db: Session,
    *,
    usuario_id: int | None,
    entidade: str,
    entidade_id: str | int | None,
    acao: AcaoAuditoria,
    dados_antes: dict | None = None,
    dados_depois: dict | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> LogAuditoria:
    """ip/user_agent: se não informados explicitamente, caem pro request atual
    (RequestContextMiddleware) — garante que toda ação auditada tenha IP, não só o login."""
    log = LogAuditoria(
        usuario_id=usuario_id,
        entidade=entidade,
        entidade_id=str(entidade_id) if entidade_id is not None else None,
        acao=acao,
        dados_antes=dados_antes,
        dados_depois=dados_depois,
        ip=ip if ip is not None else ip_atual(),
        user_agent=user_agent if user_agent is not None else user_agent_atual(),
    )
    db.add(log)
    return log
