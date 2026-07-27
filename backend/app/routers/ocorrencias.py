from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import CategoriaOcorrencia, Papel
from app.models.tipo_ocorrencia import TipoOcorrencia
from app.models.usuario import Usuario
from app.schemas.tipo_ocorrencia import TipoOcorrenciaCreate, TipoOcorrenciaOut, TipoOcorrenciaUpdate
from app.services import auditoria_service
from app.models.enums import AcaoAuditoria

router = APIRouter(prefix="/tipos-ocorrencia", tags=["ocorrencias"])


@router.get("", response_model=list[TipoOcorrenciaOut])
def listar(
    categoria: CategoriaOcorrencia | None = None,
    incluir_inativos: bool = False,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[TipoOcorrencia]:
    query = select(TipoOcorrencia)
    if not (incluir_inativos and usuario_atual.papel == Papel.KAMI_ADMIN):
        query = query.where(TipoOcorrencia.ativo.is_(True))
    if categoria:
        query = query.where(TipoOcorrencia.categoria == categoria)
    return list(db.scalars(query.order_by(TipoOcorrencia.descricao)).all())


@router.post("", response_model=TipoOcorrenciaOut, status_code=status.HTTP_201_CREATED)
def criar(
    payload: TipoOcorrenciaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> TipoOcorrencia:
    if db.scalar(select(TipoOcorrencia).where(TipoOcorrencia.codigo == payload.codigo)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um tipo de ocorrência com este código")

    tipo = TipoOcorrencia(**payload.model_dump())
    db.add(tipo)
    db.flush()

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="tipos_ocorrencia",
        entidade_id=tipo.id,
        acao=AcaoAuditoria.CREATE,
        dados_depois=payload.model_dump(mode="json"),
    )
    db.commit()
    db.refresh(tipo)
    return tipo


@router.patch("/{tipo_id}", response_model=TipoOcorrenciaOut)
def atualizar(
    tipo_id: int,
    payload: TipoOcorrenciaUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> TipoOcorrencia:
    tipo = db.get(TipoOcorrencia, tipo_id)
    if tipo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de ocorrência não encontrado")

    dados_antes = {"descricao": tipo.descricao, "ativo": tipo.ativo}
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(tipo, campo, valor)

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="tipos_ocorrencia",
        entidade_id=tipo.id,
        acao=AcaoAuditoria.UPDATE,
        dados_antes=dados_antes,
        dados_depois=payload.model_dump(exclude_unset=True, mode="json"),
    )
    db.commit()
    db.refresh(tipo)
    return tipo
