from pydantic import BaseModel

from app.models.enums import CategoriaOcorrencia


class TipoOcorrenciaOut(BaseModel):
    id: int
    categoria: CategoriaOcorrencia
    codigo: str
    descricao: str
    exige_foto: bool
    exige_observacao: bool
    ativo: bool

    model_config = {"from_attributes": True}


class TipoOcorrenciaCreate(BaseModel):
    categoria: CategoriaOcorrencia
    codigo: str
    descricao: str
    exige_foto: bool = False
    exige_observacao: bool = False


class TipoOcorrenciaUpdate(BaseModel):
    descricao: str | None = None
    exige_foto: bool | None = None
    exige_observacao: bool | None = None
    ativo: bool | None = None
