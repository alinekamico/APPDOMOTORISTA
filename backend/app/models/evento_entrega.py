from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TipoEventoEntrega, UnoSyncStatus


class EventoEntrega(Base):
    """Registro de POD (proof of delivery) de um pedido."""

    __tablename__ = "eventos_entrega"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), nullable=False)
    motorista_id: Mapped[int] = mapped_column(ForeignKey("motoristas.id"), nullable=False)

    tipo: Mapped[TipoEventoEntrega] = mapped_column(
        Enum(TipoEventoEntrega, native_enum=False, length=32), nullable=False
    )

    assinatura_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    foto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    nome_recebedor: Mapped[str | None] = mapped_column(String(255), nullable=True)

    geolocalizacao_lat: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    geolocalizacao_lng: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)

    tipo_ocorrencia_id: Mapped[int | None] = mapped_column(ForeignKey("tipos_ocorrencia.id"), nullable=True)

    uno_sync_status: Mapped[UnoSyncStatus] = mapped_column(
        Enum(UnoSyncStatus, native_enum=False, length=32),
        nullable=False,
        default=UnoSyncStatus.PENDENTE,
    )

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    pedido: Mapped["Pedido"] = relationship(back_populates="eventos_entrega")
    motorista: Mapped["Motorista"] = relationship()
