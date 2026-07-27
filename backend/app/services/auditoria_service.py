from sqlalchemy.orm import Session

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
    log = LogAuditoria(
        usuario_id=usuario_id,
        entidade=entidade,
        entidade_id=str(entidade_id) if entidade_id is not None else None,
        acao=acao,
        dados_antes=dados_antes,
        dados_depois=dados_depois,
        ip=ip,
        user_agent=user_agent,
    )
    db.add(log)
    return log
