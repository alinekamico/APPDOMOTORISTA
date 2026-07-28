from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import (
    EsqueciSenhaRequest,
    LoginRequest,
    RedefinirSenhaRequest,
    RefreshRequest,
    RefreshResponse,
    TokenResponse,
    UsuarioMeResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        usuario, access_token, refresh_token = auth_service.autenticar(db, email=payload.email, senha=payload.senha)
    except auth_service.CredenciaisInvalidasError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        papel=usuario.papel,
        nome=usuario.nome,
        transportadora_id=usuario.transportadora_id,
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> RefreshResponse:
    try:
        _usuario, novo_access_token = auth_service.renovar_access_token(db, refresh_token=payload.refresh_token)
    except auth_service.CredenciaisInvalidasError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return RefreshResponse(access_token=novo_access_token)


@router.post("/esqueci-senha", status_code=status.HTTP_202_ACCEPTED)
def esqueci_senha(payload: EsqueciSenhaRequest, db: Session = Depends(get_db)) -> dict:
    auth_service.solicitar_redefinicao_senha(db, email=payload.email)
    return {"detail": "Se o e-mail existir, um link de redefinição foi enviado."}


@router.post("/redefinir-senha", status_code=status.HTTP_204_NO_CONTENT)
def redefinir_senha(payload: RedefinirSenhaRequest, db: Session = Depends(get_db)) -> None:
    try:
        auth_service.redefinir_senha(db, raw_token=payload.token, nova_senha=payload.nova_senha)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/me", response_model=UsuarioMeResponse)
def me(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    return usuario
