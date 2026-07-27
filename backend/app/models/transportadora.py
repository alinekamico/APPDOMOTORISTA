from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Transportadora(Base):
    __tablename__ = "transportadoras"

    id: Mapped[int] = mapped_column(primary_key=True)
    razao_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nome_fantasia: Mapped[str] = mapped_column(String(255), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(18), unique=True, nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="transportadora")
    veiculos: Mapped[list["Veiculo"]] = relationship(back_populates="transportadora")
    motoristas: Mapped[list["Motorista"]] = relationship(back_populates="transportadora")
    romaneios: Mapped[list["Romaneio"]] = relationship(back_populates="transportadora")
