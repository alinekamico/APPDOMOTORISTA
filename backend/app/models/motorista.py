from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Motorista(Base):
    __tablename__ = "motoristas"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True, nullable=False)
    transportadora_id: Mapped[int] = mapped_column(ForeignKey("transportadoras.id"), nullable=False)
    cnh: Mapped[str] = mapped_column(String(20), nullable=False)
    cnh_categoria: Mapped[str] = mapped_column(String(5), nullable=False)
    telefone: Mapped[str] = mapped_column(String(20), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    usuario: Mapped["Usuario"] = relationship()
    transportadora: Mapped["Transportadora"] = relationship(back_populates="motoristas")

    @property
    def nome(self) -> str:
        return self.usuario.nome

    @property
    def email(self) -> str:
        return self.usuario.email

    @property
    def transportadora_nome(self) -> str:
        return self.transportadora.nome_fantasia
