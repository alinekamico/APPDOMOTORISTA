from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import Papel, StatusRomaneio
from app.models.motorista import Motorista
from app.models.pedido import Pedido
from app.models.tipo_ocorrencia import TipoOcorrencia
from app.models.usuario import Usuario
from app.schemas.romaneio import PedidoOut
from app.services import pod_service, resequenciamento_service, storage_service

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


def _buscar_pedido_do_motorista(db: Session, pedido_id: int, usuario_atual: Usuario) -> tuple[Pedido, Motorista]:
    pedido = db.scalar(select(Pedido).options(joinedload(Pedido.romaneio)).where(Pedido.id == pedido_id))
    if pedido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado")

    motorista = db.scalar(select(Motorista).where(Motorista.usuario_id == usuario_atual.id))
    if motorista is None or pedido.romaneio.motorista_id != motorista.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este pedido não pertence à sua rota")

    if pedido.romaneio.status != StatusRomaneio.EM_TRANSITO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="O romaneio deste pedido não está em trânsito"
        )

    return pedido, motorista


@router.post("/{pedido_id}/entrega", response_model=PedidoOut)
def registrar_entrega(
    pedido_id: int,
    foto: UploadFile = File(...),
    assinatura: UploadFile = File(...),
    nome_recebedor: str = Form(...),
    cliente_whatsapp: str | None = Form(default=None),
    cliente_email: str | None = Form(default=None),
    geolocalizacao_lat: float | None = Form(default=None),
    geolocalizacao_lng: float | None = Form(default=None),
    tipo_ocorrencia_desvio_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.MOTORISTA)),
) -> Pedido:
    pedido, motorista = _buscar_pedido_do_motorista(db, pedido_id, usuario_atual)

    foto_url = storage_service.salvar_arquivo(foto, subpasta="entregas/fotos")
    assinatura_url = storage_service.salvar_arquivo(assinatura, subpasta="entregas/assinaturas")

    try:
        return pod_service.registrar_entrega(
            db,
            pedido=pedido,
            motorista_id=motorista.id,
            foto_url=foto_url,
            assinatura_url=assinatura_url,
            nome_recebedor=nome_recebedor,
            geolocalizacao_lat=geolocalizacao_lat,
            geolocalizacao_lng=geolocalizacao_lng,
            cliente_whatsapp=cliente_whatsapp,
            cliente_email=cliente_email,
            usuario_atual=usuario_atual,
            tipo_ocorrencia_desvio_id=tipo_ocorrencia_desvio_id,
        )
    except pod_service.PedidoJaFinalizadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except resequenciamento_service.JustificativaObrigatoriaError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{pedido_id}/nao-entrega", response_model=PedidoOut)
def registrar_nao_entrega(
    pedido_id: int,
    tipo_ocorrencia_id: int = Form(...),
    observacao: str | None = Form(default=None),
    foto: UploadFile | None = File(default=None),
    geolocalizacao_lat: float | None = Form(default=None),
    geolocalizacao_lng: float | None = Form(default=None),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.MOTORISTA)),
) -> Pedido:
    pedido, motorista = _buscar_pedido_do_motorista(db, pedido_id, usuario_atual)

    tipo_ocorrencia = db.get(TipoOcorrencia, tipo_ocorrencia_id)
    if tipo_ocorrencia is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Tipo de ocorrência inválido")

    foto_url = storage_service.salvar_arquivo(foto, subpasta="entregas/nao-entrega") if foto else None

    try:
        return pod_service.registrar_nao_entrega(
            db,
            pedido=pedido,
            motorista_id=motorista.id,
            tipo_ocorrencia=tipo_ocorrencia,
            observacao=observacao,
            foto_url=foto_url,
            geolocalizacao_lat=geolocalizacao_lat,
            geolocalizacao_lng=geolocalizacao_lng,
            usuario_atual=usuario_atual,
        )
    except pod_service.PedidoJaFinalizadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except pod_service.OcorrenciaObrigatoriaError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
