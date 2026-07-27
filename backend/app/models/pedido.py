from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import StatusEntregaPedido


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    romaneio_id: Mapped[int] = mapped_column(ForeignKey("romaneios.id"), nullable=False)

    sequencia_original: Mapped[int] = mapped_column(Integer, nullable=False)
    sequencia_atual: Mapped[int] = mapped_column(Integer, nullable=False)

    status_entrega: Mapped[StatusEntregaPedido] = mapped_column(
        Enum(StatusEntregaPedido, native_enum=False, length=32),
        nullable=False,
        default=StatusEntregaPedido.PENDENTE,
    )

    cliente_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cliente_endereco: Mapped[str] = mapped_column(String(500), nullable=False)
    cliente_lat: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    cliente_lng: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    cliente_whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cliente_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Logística — nunca valores monetários (isso não deve ser exposto pra transportadora/motorista)
    peso_kg: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    qtd_volumes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    especie_volume: Mapped[str | None] = mapped_column(String(30), nullable=True)
    dt_entrega_solicitada: Mapped[date | None] = mapped_column(Date, nullable=True)

    tipo_ocorrencia_id: Mapped[int | None] = mapped_column(ForeignKey("tipos_ocorrencia.id"), nullable=True)
    entregue_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    romaneio: Mapped["Romaneio"] = relationship(back_populates="pedidos")
    eventos_entrega: Mapped[list["EventoEntrega"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan"
    )
