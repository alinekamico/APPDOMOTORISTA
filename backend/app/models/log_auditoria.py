from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AcaoAuditoria


class LogAuditoria(Base):
    """Log genérico de ações administrativas e de autenticação (governança de TI)."""

    __tablename__ = "log_auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    entidade: Mapped[str] = mapped_column(String(60), nullable=False)
    entidade_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    acao: Mapped[AcaoAuditoria] = mapped_column(Enum(AcaoAuditoria, native_enum=False, length=32), nullable=False)
    dados_antes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    dados_depois: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
