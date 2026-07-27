from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import Papel
from app.models.veiculo import Veiculo
from app.models.usuario import Usuario
from app.repositories.tenant_scope import escopar_por_transportadora
from app.schemas.veiculo import VeiculoCreate, VeiculoOut, VeiculoUpdate
from app.services import cadastro_service

router = APIRouter(prefix="/veiculos", tags=["veiculos"])


@router.get("", response_model=list[VeiculoOut])
def listar(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN, Papel.TRANSPORTADORA_ADMIN)),
) -> list[Veiculo]:
    query = escopar_por_transportadora(
        select(Veiculo).options(joinedload(Veiculo.transportadora)), Veiculo.transportadora_id, usuario_atual
    )
    return list(db.scalars(query.order_by(Veiculo.placa)).all())


@router.post("", response_model=VeiculoOut, status_code=status.HTTP_201_CREATED)
def criar(
    payload: VeiculoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.TRANSPORTADORA_ADMIN)),
) -> Veiculo:
    try:
        return cadastro_service.criar_veiculo(
            db,
            transportadora_id=usuario_atual.transportadora_id,
            placa=payload.placa,
            tipo=payload.tipo,
            capacidade_kg=payload.capacidade_kg,
            usuario_atual=usuario_atual,
        )
    except cadastro_service.RegistroDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{veiculo_id}", response_model=VeiculoOut)
def atualizar(
    veiculo_id: int,
    payload: VeiculoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.TRANSPORTADORA_ADMIN)),
) -> Veiculo:
    veiculo = db.get(Veiculo, veiculo_id)
    if veiculo is None or veiculo.transportadora_id != usuario_atual.transportadora_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado")

    return cadastro_service.atualizar_veiculo(
        db,
        veiculo=veiculo,
        tipo=payload.tipo,
        capacidade_kg=payload.capacidade_kg,
        ativo=payload.ativo,
        usuario_atual=usuario_atual,
    )
