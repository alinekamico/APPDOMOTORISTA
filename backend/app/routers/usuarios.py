from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import Papel
from app.models.usuario import Usuario
from app.schemas.usuario import KamiAdminCreate, ResetarSenhaRequest, UsuarioOut
from app.services import cadastro_service

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioOut])
def listar(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> list[Usuario]:
    """Governança: 'Perfil Admin — Admin vê tudo'. Só a KAMI enxerga todos os usuários."""
    query = select(Usuario).options(joinedload(Usuario.transportadora)).order_by(Usuario.nome)
    return list(db.scalars(query).unique().all())


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def criar_admin_kami(
    payload: KamiAdminCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> Usuario:
    try:
        return cadastro_service.criar_kami_admin(
            db,
            nome=payload.nome,
            email=payload.email,
            senha=payload.senha,
            departamento=payload.departamento,
            usuario_atual=usuario_atual,
        )
    except cadastro_service.RegistroDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{usuario_id}/senha", response_model=UsuarioOut)
def resetar_senha(
    usuario_id: int,
    payload: ResetarSenhaRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> Usuario:
    usuario_alvo = db.get(Usuario, usuario_id)
    if usuario_alvo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    return cadastro_service.resetar_senha_usuario(
        db, usuario_alvo=usuario_alvo, nova_senha=payload.senha, usuario_atual=usuario_atual
    )
