from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import CategoriaOcorrencia


class TipoOcorrencia(Base):
    __tablename__ = "tipos_ocorrencia"

    id: Mapped[int] = mapped_column(primary_key=True)
    categoria: Mapped[CategoriaOcorrencia] = mapped_column(
        Enum(CategoriaOcorrencia, native_enum=False, length=32), nullable=False
    )
    codigo: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    exige_foto: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exige_observacao: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
