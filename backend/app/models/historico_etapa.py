from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import StatusRomaneio


class HistoricoEtapa(Base):
    """Auditoria de transição de kanban do romaneio."""

    __tablename__ = "historico_etapas"

    id: Mapped[int] = mapped_column(primary_key=True)
    romaneio_id: Mapped[int] = mapped_column(ForeignKey("romaneios.id"), nullable=False)
    etapa_anterior: Mapped[StatusRomaneio | None] = mapped_column(
        Enum(StatusRomaneio, native_enum=False, length=32), nullable=True
    )
    etapa_nova: Mapped[StatusRomaneio] = mapped_column(
        Enum(StatusRomaneio, native_enum=False, length=32), nullable=False
    )
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    papel_usuario: Mapped[str | None] = mapped_column(String(32), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    romaneio: Mapped["Romaneio"] = relationship(back_populates="historico_etapas")
    usuario: Mapped["Usuario | None"] = relationship()
