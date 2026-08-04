from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.nps.stub_adapter import get_nps_notifier
from app.integrations.uno.stub_adapter import get_uno_provider
from app.models.enums import AcaoAuditoria, OrigemResequenciamento, StatusEntregaPedido, TipoEventoEntrega
from app.models.evento_entrega import EventoEntrega
from app.models.pedido import Pedido
from app.models.tipo_ocorrencia import TipoOcorrencia
from app.models.usuario import Usuario
from app.services import auditoria_service, resequenciamento_service, romaneio_service


class OcorrenciaObrigatoriaError(Exception):
    pass


class PedidoJaFinalizadoError(Exception):
    pass


def _esta_fora_de_sequencia(pedido: Pedido) -> bool:
    """Regra 1: há alguma parada anterior (na sequência vigente) ainda pendente?"""
    pendentes_anteriores = [
        p
        for p in pedido.romaneio.pedidos
        if p.id != pedido.id
        and p.sequencia_atual < pedido.sequencia_atual
        and p.status_entrega in {StatusEntregaPedido.PENDENTE, StatusEntregaPedido.EM_ROTA}
    ]
    return len(pendentes_anteriores) > 0


def registrar_entrega(
    db: Session,
    *,
    pedido: Pedido,
    motorista_id: int,
    foto_url: str,
    assinatura_url: str,
    nome_recebedor: str,
    geolocalizacao_lat: float | None,
    geolocalizacao_lng: float | None,
    cliente_whatsapp: str | None,
    cliente_email: str | None,
    mercadoria_conferida_na_entrega: bool,
    usuario_atual: Usuario,
    tipo_ocorrencia_desvio_id: int | None = None,
) -> Pedido:
    if pedido.status_entrega in {StatusEntregaPedido.ENTREGUE, StatusEntregaPedido.NAO_ENTREGUE}:
        raise PedidoJaFinalizadoError("Este pedido já foi finalizado")

    fora_de_sequencia = _esta_fora_de_sequencia(pedido)
    if fora_de_sequencia and tipo_ocorrencia_desvio_id is None:
        raise resequenciamento_service.JustificativaObrigatoriaError(
            "Esta entrega está fora da sequência prevista — informe o motivo do desvio"
        )

    evento = EventoEntrega(
        pedido_id=pedido.id,
        motorista_id=motorista_id,
        tipo=TipoEventoEntrega.ENTREGUE,
        foto_url=foto_url,
        assinatura_url=assinatura_url,
        nome_recebedor=nome_recebedor,
        geolocalizacao_lat=geolocalizacao_lat,
        geolocalizacao_lng=geolocalizacao_lng,
        mercadoria_conferida_na_entrega=mercadoria_conferida_na_entrega,
    )
    db.add(evento)

    pedido.status_entrega = StatusEntregaPedido.ENTREGUE
    pedido.entregue_em = datetime.now(timezone.utc)
    if cliente_whatsapp:
        pedido.cliente_whatsapp = cliente_whatsapp
    if cliente_email:
        pedido.cliente_email = cliente_email

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="pedidos",
        entidade_id=pedido.id,
        acao=AcaoAuditoria.UPDATE,
        dados_depois={"status_entrega": StatusEntregaPedido.ENTREGUE.value},
    )

    if fora_de_sequencia:
        posicao_atual = (
            (geolocalizacao_lat, geolocalizacao_lng)
            if geolocalizacao_lat is not None and geolocalizacao_lng is not None
            else None
        )
        try:
            resequenciamento_service.resequenciar_pendentes(
                db,
                romaneio=pedido.romaneio,
                usuario_atual=usuario_atual,
                origem=OrigemResequenciamento.DIVERGENCIA_MANUAL,
                posicao_atual=posicao_atual,
                tipo_ocorrencia_id=tipo_ocorrencia_desvio_id,
            )
        except resequenciamento_service.SemCoordenadasError:
            # Sem coordenadas suficientes pra recalcular — a justificativa já foi registrada,
            # a entrega não deve falhar por causa disso.
            pass

    romaneio_service.verificar_conclusao_automatica(db, romaneio=pedido.romaneio)

    get_uno_provider().sync(evento)
    get_nps_notifier().notify_delivery(pedido)

    db.commit()
    db.refresh(pedido)
    return pedido


def registrar_nao_entrega(
    db: Session,
    *,
    pedido: Pedido,
    motorista_id: int,
    tipo_ocorrencia: TipoOcorrencia,
    observacao: str | None,
    foto_url: str | None,
    geolocalizacao_lat: float | None,
    geolocalizacao_lng: float | None,
    usuario_atual: Usuario,
) -> Pedido:
    if pedido.status_entrega in {StatusEntregaPedido.ENTREGUE, StatusEntregaPedido.NAO_ENTREGUE}:
        raise PedidoJaFinalizadoError("Este pedido já foi finalizado")

    if tipo_ocorrencia.exige_observacao and not observacao:
        raise OcorrenciaObrigatoriaError("Este tipo de ocorrência exige uma observação")
    if tipo_ocorrencia.exige_foto and not foto_url:
        raise OcorrenciaObrigatoriaError("Este tipo de ocorrência exige uma foto")

    evento = EventoEntrega(
        pedido_id=pedido.id,
        motorista_id=motorista_id,
        tipo=TipoEventoEntrega.NAO_ENTREGUE,
        foto_url=foto_url,
        geolocalizacao_lat=geolocalizacao_lat,
        geolocalizacao_lng=geolocalizacao_lng,
        tipo_ocorrencia_id=tipo_ocorrencia.id,
    )
    db.add(evento)

    pedido.status_entrega = StatusEntregaPedido.NAO_ENTREGUE
    pedido.tipo_ocorrencia_id = tipo_ocorrencia.id
    pedido.entregue_em = datetime.now(timezone.utc)

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="pedidos",
        entidade_id=pedido.id,
        acao=AcaoAuditoria.UPDATE,
        dados_depois={"status_entrega": StatusEntregaPedido.NAO_ENTREGUE.value, "tipo_ocorrencia": tipo_ocorrencia.codigo},
    )

    romaneio_service.verificar_conclusao_automatica(db, romaneio=pedido.romaneio)

    db.commit()
    db.refresh(pedido)
    return pedido
