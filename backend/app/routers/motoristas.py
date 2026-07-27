from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import Papel
from app.models.motorista import Motorista
from app.models.usuario import Usuario
from app.repositories.tenant_scope import escopar_por_transportadora
from app.schemas.motorista import MotoristaCreate, MotoristaOut, MotoristaUpdate
from app.services import cadastro_service

router = APIRouter(prefix="/motoristas", tags=["motoristas"])


@router.get("", response_model=list[MotoristaOut])
def listar(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN, Papel.TRANSPORTADORA_ADMIN)),
) -> list[Motorista]:
    query = escopar_por_transportadora(
        select(Motorista).options(joinedload(Motorista.usuario), joinedload(Motorista.transportadora)),
        Motorista.transportadora_id,
        usuario_atual,
    )
    return list(db.scalars(query).unique().all())


@router.post("", response_model=MotoristaOut, status_code=status.HTTP_201_CREATED)
def criar(
    payload: MotoristaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.TRANSPORTADORA_ADMIN)),
) -> Motorista:
    try:
        return cadastro_service.criar_motorista(
            db,
            transportadora_id=usuario_atual.transportadora_id,
            nome=payload.nome,
            email=payload.email,
            senha=payload.senha,
            cnh=payload.cnh,
            cnh_categoria=payload.cnh_categoria,
            telefone=payload.telefone,
            usuario_atual=usuario_atual,
        )
    except cadastro_service.RegistroDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{motorista_id}", response_model=MotoristaOut)
def atualizar(
    motorista_id: int,
    payload: MotoristaUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.TRANSPORTADORA_ADMIN)),
) -> Motorista:
    motorista = db.get(Motorista, motorista_id)
    if motorista is None or motorista.transportadora_id != usuario_atual.transportadora_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motorista não encontrado")

    return cadastro_service.atualizar_motorista(
        db,
        motorista=motorista,
        telefone=payload.telefone,
        ativo=payload.ativo,
        senha=payload.senha,
        usuario_atual=usuario_atual,
    )
