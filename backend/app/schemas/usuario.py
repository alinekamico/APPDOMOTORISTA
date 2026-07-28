from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import Papel


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str
    papel: Papel
    departamento: str | None
    transportadora_nome: str | None
    ativo: bool
    criado_em: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class KamiAdminCreate(BaseModel):
    """KAMI cria outro usuário kami_admin — governança: 'Admin cria usuários'."""

    nome: str
    email: EmailStr
    senha: str = Field(min_length=8)
    departamento: str | None = None


class ResetarSenhaRequest(BaseModel):
    senha: str = Field(min_length=8)
