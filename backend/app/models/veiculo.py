from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Veiculo(Base):
    __tablename__ = "veiculos"

    id: Mapped[int] = mapped_column(primary_key=True)
    transportadora_id: Mapped[int] = mapped_column(ForeignKey("transportadoras.id"), nullable=False)
    placa: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(60), nullable=False)
    capacidade_kg: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    transportadora: Mapped["Transportadora"] = relationship(back_populates="veiculos")

    @property
    def transportadora_nome(self) -> str:
        return self.transportadora.nome_fantasia
