from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import Papel
from app.models.transportadora import Transportadora
from app.models.usuario import Usuario
from app.schemas.auth import UsuarioMeResponse
from app.schemas.transportadora import TransportadoraAdminCreate, TransportadoraCreate, TransportadoraOut
from app.services import cadastro_service

router = APIRouter(prefix="/transportadoras", tags=["transportadoras"])


@router.get("", response_model=list[TransportadoraOut])
def listar(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> list[Transportadora]:
    return list(db.scalars(select(Transportadora).order_by(Transportadora.nome_fantasia)).all())


@router.post("", response_model=TransportadoraOut, status_code=status.HTTP_201_CREATED)
def criar(
    payload: TransportadoraCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> Transportadora:
    try:
        return cadastro_service.criar_transportadora(
            db,
            razao_social=payload.razao_social,
            nome_fantasia=payload.nome_fantasia,
            cnpj=payload.cnpj,
            usuario_atual=usuario_atual,
        )
    except cadastro_service.RegistroDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/sincronizar-uno")
def sincronizar_uno(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> dict:
    """Busca todas as transportadoras cadastradas na réplica do UNO e cadastra as que
    ainda não existem aqui."""
    return cadastro_service.sincronizar_transportadoras_da_fonte_externa(db, usuario_atual=usuario_atual)


@router.post("/{transportadora_id}/admins", response_model=UsuarioMeResponse, status_code=status.HTTP_201_CREATED)
def criar_admin(
    transportadora_id: int,
    payload: TransportadoraAdminCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> Usuario:
    transportadora = db.get(Transportadora, transportadora_id)
    if transportadora is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transportadora não encontrada")

    try:
        return cadastro_service.criar_admin_transportadora(
            db,
            transportadora_id=transportadora_id,
            nome=payload.nome,
            email=payload.email,
            senha=payload.senha,
            departamento=payload.departamento,
            usuario_atual=usuario_atual,
        )
    except cadastro_service.RegistroDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
