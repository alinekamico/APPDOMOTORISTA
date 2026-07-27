from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import AcaoAuditoria, OrigemRomaneio, StatusEntregaPedido, StatusRomaneio
from app.models.foto_carregamento import FotoCarregamento
from app.models.historico_etapa import HistoricoEtapa
from app.models.motorista import Motorista
from app.models.pedido import Pedido
from app.models.romaneio import Romaneio
from app.models.transportadora import Transportadora
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.schemas.romaneio import PedidoCreateItem, RomaneioCriarRequest
from app.services import auditoria_service


class RomaneioDuplicadoError(Exception):
    pass


class TransportadoraInvalidaError(Exception):
    pass


class TransicaoInvalidaError(Exception):
    pass


class RecursoInvalidoError(Exception):
    pass


class EvidenciaObrigatoriaError(Exception):
    pass


def _transicionar(
    db: Session,
    *,
    romaneio: Romaneio,
    novo_status: StatusRomaneio,
    usuario_atual: Usuario | None,
    observacao: str | None = None,
) -> None:
    historico = HistoricoEtapa(
        romaneio_id=romaneio.id,
        etapa_anterior=romaneio.status,
        etapa_nova=novo_status,
        usuario_id=usuario_atual.id if usuario_atual else None,
        papel_usuario=usuario_atual.papel.value if usuario_atual else "sistema",
        observacao=observacao,
    )
    db.add(historico)
    romaneio.status = novo_status

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id if usuario_atual else None,
        entidade="romaneios",
        entidade_id=romaneio.id,
        acao=AcaoAuditoria.TRANSICAO_ETAPA,
        dados_antes={"status": historico.etapa_anterior.value if historico.etapa_anterior else None},
        dados_depois={"status": novo_status.value},
    )


def _rotear_automaticamente(
    pedidos: list[PedidoCreateItem], *, origem_lat: float | None, origem_lng: float | None
) -> list[PedidoCreateItem]:
    """Regra 3: a sequência de entrega é calculada pelo sistema, não digitada por quem cria
    o romaneio — quem cria só informa endereços/pesos e o ponto de partida. Usa o mesmo
    heurístico do resequenciamento em rota (nearest-neighbor + 2-opt).

    Sem `origem_lat`/`origem_lng`, ou se algum pedido não tiver coordenadas, mantém a ordem
    em que os pedidos foram informados (não dá pra rotear sem saber de onde o veículo parte
    e para onde cada parada vai).
    """
    if origem_lat is None or origem_lng is None:
        return pedidos
    if any(p.cliente_lat is None or p.cliente_lng is None for p in pedidos):
        return pedidos
    if len(pedidos) <= 1:
        return pedidos

    from app.integrations.maps import get_maps_provider
    from app.services.resequenciamento_service import calcular_sequencia_otima

    pontos = [(origem_lat, origem_lng)] + [(p.cliente_lat, p.cliente_lng) for p in pedidos]
    matriz = get_maps_provider().obter_matriz_duracao(pontos)
    ordem = calcular_sequencia_otima(matriz)  # índices 1..N relativos a `pontos`/`pedidos`

    pedidos_ordenados = []
    for posicao, indice in enumerate(ordem):
        item = pedidos[indice - 1]
        item.sequencia = posicao + 1
        pedidos_ordenados.append(item)
    return pedidos_ordenados


def criar_de_comando(
    db: Session,
    *,
    comando: RomaneioCriarRequest,
    origem: OrigemRomaneio,
    usuario_atual: Usuario | None,
) -> Romaneio:
    if db.scalar(select(Romaneio).where(Romaneio.codigo == comando.codigo)):
        raise RomaneioDuplicadoError(f"Já existe um romaneio com o código {comando.codigo}")

    if db.get(Transportadora, comando.transportadora_id) is None:
        raise TransportadoraInvalidaError("Transportadora informada não existe")

    # Se o cabeçalho não veio com qtd_caixas/peso_total explícitos (caso comum na importação
    # do UNO, que só traz esses valores por pedido), soma a partir dos próprios pedidos.
    qtd_caixas = comando.qtd_caixas
    if qtd_caixas is None:
        soma_volumes = sum(p.qtd_volumes or 0 for p in comando.pedidos)
        qtd_caixas = soma_volumes if soma_volumes > 0 else None

    peso_total = comando.peso_total
    if peso_total is None:
        soma_peso = sum(p.peso_kg or 0 for p in comando.pedidos)
        peso_total = soma_peso if soma_peso > 0 else None

    romaneio = Romaneio(
        codigo=comando.codigo,
        transportadora_id=comando.transportadora_id,
        status=StatusRomaneio.DEFINICAO_TRANSPORTE,
        origem=origem,
        tms_referencia_externa=comando.tms_referencia_externa,
        qtd_caixas=qtd_caixas,
        qtd_pedidos=len(comando.pedidos),
        peso_total=peso_total,
        tipo_veiculo_sugerido=comando.tipo_veiculo_sugerido,
        data_saida_prevista=comando.data_saida_prevista,
    )
    db.add(romaneio)
    db.flush()

    pedidos_ordenados = _rotear_automaticamente(
        comando.pedidos, origem_lat=comando.origem_lat, origem_lng=comando.origem_lng
    )

    for item in pedidos_ordenados:
        pedido = Pedido(
            romaneio_id=romaneio.id,
            sequencia_original=item.sequencia,
            sequencia_atual=item.sequencia,
            cliente_nome=item.cliente_nome,
            cliente_endereco=item.cliente_endereco,
            cliente_lat=item.cliente_lat,
            cliente_lng=item.cliente_lng,
            cliente_whatsapp=item.cliente_whatsapp,
            cliente_email=item.cliente_email,
            peso_kg=item.peso_kg,
            qtd_volumes=item.qtd_volumes,
            especie_volume=item.especie_volume,
            dt_entrega_solicitada=item.dt_entrega_solicitada,
        )
        db.add(pedido)

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id if usuario_atual else None,
        entidade="romaneios",
        entidade_id=romaneio.id,
        acao=AcaoAuditoria.CREATE,
        dados_depois={"codigo": comando.codigo, "origem": origem.value, "qtd_pedidos": len(comando.pedidos)},
    )
    db.commit()
    db.refresh(romaneio)
    return romaneio


def buscar_com_pedidos(db: Session, romaneio_id: int) -> Romaneio | None:
    return db.scalar(
        select(Romaneio)
        .options(
            selectinload(Romaneio.pedidos),
            selectinload(Romaneio.transportadora),
            selectinload(Romaneio.veiculo),
            selectinload(Romaneio.motorista).selectinload(Motorista.usuario),
            selectinload(Romaneio.fotos_carregamento),
        )
        .where(Romaneio.id == romaneio_id)
    )


def alterar_transportadora(
    db: Session, *, romaneio: Romaneio, nova_transportadora_id: int, usuario_atual: Usuario
) -> Romaneio:
    """KAMI corrige/reatribui qual transportadora vai atender o romaneio — só antes de haver
    veículo/motorista alocados (ou seja, ainda em definição de transporte), pra não deixar um
    veículo/motorista de uma transportadora vinculado a outra."""
    if romaneio.status != StatusRomaneio.DEFINICAO_TRANSPORTE:
        raise TransicaoInvalidaError(
            "Só é possível trocar a transportadora enquanto o romaneio está em definição de transporte"
        )

    nova_transportadora = db.get(Transportadora, nova_transportadora_id)
    if nova_transportadora is None:
        raise TransportadoraInvalidaError("Transportadora informada não existe")

    transportadora_anterior_id = romaneio.transportadora_id
    romaneio.transportadora_id = nova_transportadora_id

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="romaneios",
        entidade_id=romaneio.id,
        acao=AcaoAuditoria.UPDATE,
        dados_antes={"transportadora_id": transportadora_anterior_id},
        dados_depois={"transportadora_id": nova_transportadora_id},
    )
    db.commit()
    db.refresh(romaneio)
    return romaneio


def alocar_veiculo_motorista(
    db: Session, *, romaneio: Romaneio, veiculo_id: int, motorista_id: int, usuario_atual: Usuario
) -> Romaneio:
    """Etapa 1 → 2: a transportadora indica veículo e motorista (Regra 6: só da própria frota)."""
    if romaneio.status != StatusRomaneio.DEFINICAO_TRANSPORTE:
        raise TransicaoInvalidaError("Romaneio não está na etapa de definição de transporte")

    veiculo = db.get(Veiculo, veiculo_id)
    if veiculo is None or veiculo.transportadora_id != romaneio.transportadora_id:
        raise RecursoInvalidoError("Veículo não pertence a esta transportadora")

    motorista = db.get(Motorista, motorista_id)
    if motorista is None or motorista.transportadora_id != romaneio.transportadora_id:
        raise RecursoInvalidoError("Motorista não pertence a esta transportadora")

    romaneio.veiculo_id = veiculo_id
    romaneio.motorista_id = motorista_id
    _transicionar(db, romaneio=romaneio, novo_status=StatusRomaneio.CONFERENCIA_LOGISTICA, usuario_atual=usuario_atual)

    db.commit()
    db.refresh(romaneio)
    return romaneio


def devolver_para_definicao_transporte(
    db: Session, *, romaneio: Romaneio, usuario_atual: Usuario, observacao: str | None = None
) -> Romaneio:
    """Etapa 2 → 1: KAMI devolve o romaneio na conferência para a transportadora corrigir
    veículo/motorista (ex: motorista errado, veículo não bate com o do portão)."""
    if romaneio.status != StatusRomaneio.CONFERENCIA_LOGISTICA:
        raise TransicaoInvalidaError("Romaneio não está na etapa de conferência logística")

    romaneio.veiculo_id = None
    romaneio.motorista_id = None
    _transicionar(
        db,
        romaneio=romaneio,
        novo_status=StatusRomaneio.DEFINICAO_TRANSPORTE,
        usuario_atual=usuario_atual,
        observacao=observacao,
    )

    db.commit()
    db.refresh(romaneio)
    return romaneio


def confirmar_conferencia_logistica(db: Session, *, romaneio: Romaneio, usuario_atual: Usuario) -> Romaneio:
    """Etapa 2 → 3: KAMI confere no portão que motorista/veículo batem com o indicado."""
    if romaneio.status != StatusRomaneio.CONFERENCIA_LOGISTICA:
        raise TransicaoInvalidaError("Romaneio não está na etapa de conferência logística")

    romaneio.conferencia_em = datetime.now(timezone.utc)
    _transicionar(db, romaneio=romaneio, novo_status=StatusRomaneio.CARREGAMENTO, usuario_atual=usuario_atual)

    db.commit()
    db.refresh(romaneio)
    return romaneio


def adicionar_foto_carregamento(
    db: Session, *, romaneio: Romaneio, foto_url: str, usuario_atual: Usuario
) -> Romaneio:
    """Motorista registra uma foto evidenciando o carregamento — pode chamar quantas vezes precisar,
    sem transicionar a etapa (a transição só acontece quando ele confirma o fim do carregamento)."""
    if romaneio.status != StatusRomaneio.CARREGAMENTO:
        raise TransicaoInvalidaError("Romaneio não está na etapa de carregamento")

    db.add(FotoCarregamento(romaneio_id=romaneio.id, foto_url=foto_url))
    db.commit()
    db.refresh(romaneio)
    return romaneio


def finalizar_carregamento(db: Session, *, romaneio: Romaneio, usuario_atual: Usuario) -> Romaneio:
    """Etapa 3 → 4: motorista confirma o fim do carregamento; romaneio vai direto pra iniciar rota."""
    if romaneio.status != StatusRomaneio.CARREGAMENTO:
        raise TransicaoInvalidaError("Romaneio não está na etapa de carregamento")
    if not romaneio.fotos_carregamento:
        raise EvidenciaObrigatoriaError("Registre ao menos uma foto do carregamento antes de finalizar")

    romaneio.carregamento_em = datetime.now(timezone.utc)
    _transicionar(db, romaneio=romaneio, novo_status=StatusRomaneio.INICIO_ROTA, usuario_atual=usuario_atual)

    db.commit()
    db.refresh(romaneio)
    return romaneio


def iniciar_rota(db: Session, *, romaneio: Romaneio, usuario_atual: Usuario) -> Romaneio:
    """Etapa 4 → 5: motorista dá início efetivo à rota (Regra 3: sequência já vem definida do TMS)."""
    if romaneio.status != StatusRomaneio.INICIO_ROTA:
        raise TransicaoInvalidaError("Romaneio não está pronto para iniciar rota")

    romaneio.inicio_rota_em = datetime.now(timezone.utc)
    _transicionar(db, romaneio=romaneio, novo_status=StatusRomaneio.EM_TRANSITO, usuario_atual=usuario_atual)

    db.commit()
    db.refresh(romaneio)
    return romaneio


_ETAPAS_COM_EXECUCAO_EM_CAMPO = {
    StatusRomaneio.CARREGAMENTO,
    StatusRomaneio.INICIO_ROTA,
    StatusRomaneio.EM_TRANSITO,
}


def reportar_problema(
    db: Session,
    *,
    romaneio: Romaneio,
    novo_status: StatusRomaneio,
    tipo_ocorrencia_id: int,
    observacao: str,
    usuario_atual: Usuario,
) -> Romaneio:
    """Motorista aciona `romaneio_incompleto` (entrega parcial por pane/saúde) ou
    `romaneio_com_problema` (outra exceção) — em qualquer ponto da execução em campo."""
    if novo_status not in {StatusRomaneio.ROMANEIO_INCOMPLETO, StatusRomaneio.ROMANEIO_COM_PROBLEMA}:
        raise TransicaoInvalidaError("Status informado não é um estado de exceção válido")
    if romaneio.status not in _ETAPAS_COM_EXECUCAO_EM_CAMPO:
        raise TransicaoInvalidaError("Só é possível reportar problema durante a execução em campo do romaneio")

    romaneio.tipo_ocorrencia_id = tipo_ocorrencia_id
    romaneio.observacao_ocorrencia = observacao
    _transicionar(db, romaneio=romaneio, novo_status=novo_status, usuario_atual=usuario_atual, observacao=observacao)

    db.commit()
    db.refresh(romaneio)
    return romaneio


def listar_para_motorista(db: Session, *, motorista_id: int) -> list[Romaneio]:
    return list(
        db.scalars(
            select(Romaneio)
            .options(
                selectinload(Romaneio.transportadora),
                selectinload(Romaneio.veiculo),
                selectinload(Romaneio.motorista).selectinload(Motorista.usuario),
            )
            .where(Romaneio.motorista_id == motorista_id)
            .order_by(Romaneio.criado_em.desc())
        ).all()
    )


def verificar_conclusao_automatica(db: Session, *, romaneio: Romaneio) -> None:
    """Regra do sistema: quando 100% dos pedidos estiverem finalizados, o romaneio conclui sozinho."""
    pedidos = romaneio.pedidos
    if not pedidos or romaneio.status != StatusRomaneio.EM_TRANSITO:
        return

    finalizados = {StatusEntregaPedido.ENTREGUE, StatusEntregaPedido.NAO_ENTREGUE, StatusEntregaPedido.CANCELADO}
    if all(p.status_entrega in finalizados for p in pedidos):
        romaneio.concluido_em = datetime.now(timezone.utc)
        _transicionar(db, romaneio=romaneio, novo_status=StatusRomaneio.CONCLUIDO, usuario_atual=None)


def inserir_pedidos(
    db: Session, *, romaneio: Romaneio, novos_pedidos: list[PedidoCreateItem], usuario_atual: Usuario
) -> Romaneio:
    """Regra 7: adiciona parada(s) a um romaneio já em andamento."""
    if romaneio.status in {StatusRomaneio.CONCLUIDO, StatusRomaneio.ROMANEIO_INCOMPLETO, StatusRomaneio.ROMANEIO_COM_PROBLEMA}:
        raise TransicaoInvalidaError("Não é possível inserir pedidos em um romaneio já finalizado")

    proxima_sequencia = max((p.sequencia_atual for p in romaneio.pedidos), default=0) + 1
    for offset, item in enumerate(novos_pedidos):
        pedido = Pedido(
            romaneio_id=romaneio.id,
            sequencia_original=proxima_sequencia + offset,
            sequencia_atual=proxima_sequencia + offset,
            cliente_nome=item.cliente_nome,
            cliente_endereco=item.cliente_endereco,
            cliente_lat=item.cliente_lat,
            cliente_lng=item.cliente_lng,
            cliente_whatsapp=item.cliente_whatsapp,
            cliente_email=item.cliente_email,
            peso_kg=item.peso_kg,
            qtd_volumes=item.qtd_volumes,
            especie_volume=item.especie_volume,
            dt_entrega_solicitada=item.dt_entrega_solicitada,
        )
        db.add(pedido)

    romaneio.qtd_pedidos = (romaneio.qtd_pedidos or 0) + len(novos_pedidos)
    soma_volumes = sum(p.qtd_volumes or 0 for p in novos_pedidos)
    if soma_volumes:
        romaneio.qtd_caixas = (romaneio.qtd_caixas or 0) + soma_volumes
    soma_peso = sum(p.peso_kg or 0 for p in novos_pedidos)
    if soma_peso:
        romaneio.peso_total = float(romaneio.peso_total or 0) + soma_peso

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="romaneios",
        entidade_id=romaneio.id,
        acao=AcaoAuditoria.UPDATE,
        dados_depois={"pedidos_inseridos": len(novos_pedidos)},
    )

    db.commit()
    db.refresh(romaneio)
    return romaneio


class ResultadoImportacao:
    def __init__(self) -> None:
        self.importados: list[str] = []
        self.ignorados: list[dict] = []

    def to_dict(self) -> dict:
        return {"importados": self.importados, "ignorados": self.ignorados}


def _somente_digitos(valor: str) -> str:
    return "".join(ch for ch in valor if ch.isdigit())


def importar_de_fonte_externa(db: Session, *, usuario_atual: Usuario) -> ResultadoImportacao:
    """Busca romaneios na fonte externa configurada (hoje: réplica do UNO no Supabase;
    padrão: nenhuma, retorna vazio) e cria os que ainda não existem — casando a
    transportadora pelo CNPJ (comparado só pelos dígitos, já que o UNO manda sem pontuação
    e o nosso cadastro guarda formatado). Duplicados (já importados) e CNPJ desconhecido são
    reportados em `ignorados`, sem derrubar o restante do lote.
    """
    from app.integrations.uno_source import get_romaneio_source
    from app.schemas.romaneio import PedidoCreateItem as _PedidoItem

    resultado = ResultadoImportacao()
    externos = get_romaneio_source().buscar_romaneios_pendentes()

    transportadoras_por_cnpj = {
        _somente_digitos(t.cnpj): t for t in db.scalars(select(Transportadora)).all()
    }

    for externo in externos:
        transportadora = transportadoras_por_cnpj.get(_somente_digitos(externo.transportadora_cnpj))
        if transportadora is None:
            resultado.ignorados.append(
                {"codigo": externo.codigo, "motivo": f"CNPJ {externo.transportadora_cnpj} não cadastrado"}
            )
            continue

        comando = RomaneioCriarRequest(
            codigo=externo.codigo,
            transportadora_id=transportadora.id,
            qtd_caixas=externo.qtd_caixas,
            peso_total=externo.peso_total,
            tms_referencia_externa=externo.referencia_externa,
            tipo_veiculo_sugerido=externo.tipo_veiculo_sugerido,
            data_saida_prevista=externo.data_saida_prevista,
            pedidos=[_PedidoItem(**p.model_dump()) for p in externo.pedidos],
        )

        try:
            criar_de_comando(db, comando=comando, origem=OrigemRomaneio.UNO_REPLICA, usuario_atual=usuario_atual)
            resultado.importados.append(externo.codigo)
        except RomaneioDuplicadoError:
            resultado.ignorados.append({"codigo": externo.codigo, "motivo": "já importado anteriormente"})

    return resultado
