from pydantic import BaseModel, EmailStr, Field


class MotoristaCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str = Field(min_length=8)
    cnh: str
    cnh_categoria: str
    telefone: str


class MotoristaUpdate(BaseModel):
    telefone: str | None = None
    ativo: bool | None = None
    senha: str | None = Field(default=None, min_length=8)


class MotoristaOut(BaseModel):
    id: int
    usuario_id: int
    transportadora_id: int
    transportadora_nome: str
    nome: str
    email: str
    cnh: str
    cnh_categoria: str
    telefone: str
    ativo: bool

    model_config = {"from_attributes": True}
