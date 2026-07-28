from pydantic import BaseModel, EmailStr, Field

from app.models.enums import Papel


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    papel: Papel
    nome: str
    transportadora_id: int | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EsqueciSenhaRequest(BaseModel):
    email: EmailStr


class RedefinirSenhaRequest(BaseModel):
    token: str
    nova_senha: str = Field(min_length=8)


class UsuarioMeResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    papel: Papel
    transportadora_id: int | None = None
    departamento: str | None = None

    model_config = {"from_attributes": True}
