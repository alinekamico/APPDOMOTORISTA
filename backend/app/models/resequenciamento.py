from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import OrigemResequenciamento


class Resequenciamento(Base):
    """Auditoria de todo recálculo de sequência de entrega (Regras 1, 4 e 7)."""

    __tablename__ = "resequenciamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    romaneio_id: Mapped[int] = mapped_column(ForeignKey("romaneios.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)

    origem: Mapped[OrigemResequenciamento] = mapped_column(
        Enum(OrigemResequenciamento, native_enum=False, length=32), nullable=False
    )

    sequencia_antes: Mapped[list] = mapped_column(JSON, nullable=False)
    sequencia_depois: Mapped[list] = mapped_column(JSON, nullable=False)

    # Obrigatório quando origem=divergencia_manual (Regra 1)
    tipo_ocorrencia_id: Mapped[int | None] = mapped_column(ForeignKey("tipos_ocorrencia.id"), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    distancia_estimada_km: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    tempo_estimado_min: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    romaneio: Mapped["Romaneio"] = relationship(back_populates="resequenciamentos")
    usuario: Mapped["Usuario"] = relationship()
