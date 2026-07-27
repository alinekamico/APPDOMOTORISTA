from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FotoCarregamento(Base):
    """Evidência fotográfica do carregamento — um romaneio pode ter várias."""

    __tablename__ = "fotos_carregamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    romaneio_id: Mapped[int] = mapped_column(ForeignKey("romaneios.id"), nullable=False)
    foto_url: Mapped[str] = mapped_column(String(500), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    romaneio: Mapped["Romaneio"] = relationship(back_populates="fotos_carregamento")
