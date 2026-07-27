from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TransportadoraCreate(BaseModel):
    razao_social: str
    nome_fantasia: str
    cnpj: str = Field(min_length=14, max_length=18)


class TransportadoraOut(BaseModel):
    id: int
    razao_social: str
    nome_fantasia: str
    cnpj: str
    ativo: bool
    criado_em: datetime

    model_config = {"from_attributes": True}


class TransportadoraAdminCreate(BaseModel):
    """Cria o primeiro (ou mais um) usuário transportadora_admin para uma transportadora."""

    nome: str
    email: EmailStr
    senha: str = Field(min_length=8)
    departamento: str | None = None
