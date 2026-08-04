from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import (
    AcaoAuditoria,
    CategoriaOcorrencia,
    OrigemRomaneio,
    StatusEntregaPedido,
    StatusRomaneio,
    TipoEventoEntrega,
)
from app.models.evento_entrega import EventoEntrega
from app.models.foto_carregamento import FotoCarregamento
from app.models.historico_etapa import HistoricoEtapa
from app.models.motorista import Motorista
from app.models.pedido import Pedido
from app.models.romaneio import Romaneio
from app.models.tipo_ocorrencia import TipoOcorrencia
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


class PedidosPendentesError(Exception):
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

    if comando.transportadora_id is not None and db.get(Transportadora, comando.transportadora_id) is None:
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

    # Sem transportadora casada (CNPJ desconhecido, ainda): entra em "definição da
    # transportadora" pra KAMI atribuir manualmente — no futuro, com o cadastro de
    # transportadoras completo, isso deixa de acontecer e vai direto pra definição de
    # transporte, como já ocorre quando o CNPJ já é conhecido.
    status_inicial = (
        StatusRomaneio.DEFINICAO_TRANSPORTE
        if comando.transportadora_id is not None
        else StatusRomaneio.DEFINICAO_TRANSPORTADORA
    )

    romaneio = Romaneio(
        codigo=comando.codigo,
        transportadora_id=comando.transportadora_id,
        transportadora_cnpj_externo=comando.transportadora_cnpj_externo,
        status=status_inicial,
        origem=origem,
        tms_referencia_externa=comando.tms_referencia_externa,
        qtd_caixas=qtd_caixas,
        qtd_pedidos=len(comando.pedidos),
        peso_total=peso_total,
        tipo_veiculo_sugerido=comando.tipo_veiculo_sugerido,
        data_saida_prevista=comando.data_saida_prevista,
        empresa_nome=comando.empresa_nome,
        empresa_uf=comando.empresa_uf,
    )
    db.add(romaneio)
    db.flush()

    pedidos_ordenados = _rotear_automaticamente(
        comando.pedidos, origem_lat=comando.origem_lat, origem_lng=comando.origem_lng
    )

    # O UNO não sequencia boa parte dos pedidos (manda "ordem" zerada/repetida pra vários
    # deles) — renumeramos 1..N na ordem em que chegaram (preservando a ordem parcial que o
    # UNO deu, via QUERY_PEDIDOS ORDER BY ordem) pra garantir uma sequência sempre limpa e
    # sem duplicatas exibida ao motorista. Quando _rotear_automaticamente já roteirizou de
    # verdade (1..N sem lacunas), isso é um no-op.
    for posicao, item in enumerate(pedidos_ordenados, start=1):
        item.sequencia = posicao

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


def finalizar_romaneio(
    db: Session,
    *,
    romaneio: Romaneio,
    motorista_id: int,
    usuario_atual: Usuario,
    tipo_ocorrencia_id: int | None = None,
    observacao: str | None = None,
) -> Romaneio:
    """Motorista indica que concluiu o romaneio (ou que não vai conseguir continuar).

    Se ainda houver pedido pendente/em rota, não bloqueia — pede um motivo:
    - Motivo de categoria "não entrega" (cliente ausente, endereço não localizado etc.):
      aplica a todos os pendentes de uma vez, marcando-os como não entregues. Se 100% acabar
      entregue, conclui de vez (`concluido`, bloqueado); havendo não entregue, vai para
      `romaneio_incompleto` — a KAMI decide o que fazer com as pendências.
    - Motivo de categoria "problema do romaneio" (pane, acidente, saúde, furto/roubo): não
      mexe nos pedidos — vai direto pra `romaneio_com_problema`, tirando a responsabilidade do
      motorista (a transportadora/KAMI assume dali pra frente, decidindo se reagenda a entrega
      pro dia seguinte ou se o motorista deve devolver a mercadoria). O frontend já pergunta
      antes "vai conseguir continuar hoje?" — só chama esse motivo se a resposta for não.
    """
    if romaneio.status != StatusRomaneio.EM_TRANSITO:
        raise TransicaoInvalidaError("Só é possível finalizar um romaneio em trânsito")

    tipo_ocorrencia: TipoOcorrencia | None = None
    if tipo_ocorrencia_id is not None:
        tipo_ocorrencia = db.get(TipoOcorrencia, tipo_ocorrencia_id)
        if tipo_ocorrencia is None:
            raise RecursoInvalidoError("Tipo de ocorrência inválido")
        if tipo_ocorrencia.exige_observacao and not observacao:
            raise PedidosPendentesError("Este motivo exige uma descrição")

    if tipo_ocorrencia is not None and tipo_ocorrencia.categoria == CategoriaOcorrencia.PROBLEMA_ROMANEIO:
        romaneio.tipo_ocorrencia_id = tipo_ocorrencia.id
        romaneio.observacao_ocorrencia = observacao
        _transicionar(
            db, romaneio=romaneio, novo_status=StatusRomaneio.ROMANEIO_COM_PROBLEMA,
            usuario_atual=usuario_atual, observacao=observacao,
        )
        db.commit()
        db.refresh(romaneio)
        return romaneio

    pedidos = romaneio.pedidos
    pendentes = [p for p in pedidos if p.status_entrega in {StatusEntregaPedido.PENDENTE, StatusEntregaPedido.EM_ROTA}]

    if pendentes:
        if tipo_ocorrencia is None:
            raise PedidosPendentesError(
                f"Ainda há {len(pendentes)} pedido(s) sem confirmação de entrega — "
                "informe o motivo pra finalizar o romaneio marcando-os como não entregues"
            )

        agora = datetime.now(timezone.utc)
        for pedido in pendentes:
            pedido.status_entrega = StatusEntregaPedido.NAO_ENTREGUE
            pedido.tipo_ocorrencia_id = tipo_ocorrencia.id
            pedido.entregue_em = agora
            db.add(
                EventoEntrega(
                    pedido_id=pedido.id,
                    motorista_id=motorista_id,
                    tipo=TipoEventoEntrega.NAO_ENTREGUE,
                    tipo_ocorrencia_id=tipo_ocorrencia.id,
                    observacao=observacao,
                )
            )

    todos_entregues = all(p.status_entrega == StatusEntregaPedido.ENTREGUE for p in pedidos)
    novo_status = StatusRomaneio.CONCLUIDO if todos_entregues else StatusRomaneio.ROMANEIO_INCOMPLETO

    romaneio.concluido_em = datetime.now(timezone.utc)
    _transicionar(db, romaneio=romaneio, novo_status=novo_status, usuario_atual=usuario_atual)

    db.commit()
    db.refresh(romaneio)
    return romaneio


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
        self.aguardando_transportadora: list[str] = []
        self.reatribuidos: list[str] = []
        self.ignorados: list[dict] = []

    def to_dict(self) -> dict:
        return {
            "importados": self.importados,
            "aguardando_transportadora": self.aguardando_transportadora,
            "reatribuidos": self.reatribuidos,
            "ignorados": self.ignorados,
        }


def _somente_digitos(valor: str) -> str:
    return "".join(ch for ch in valor if ch.isdigit())


def importar_de_fonte_externa(db: Session, *, usuario_atual: Usuario | None) -> ResultadoImportacao:
    """Busca romaneios na fonte externa configurada (hoje: réplica do UNO no Supabase;
    padrão: nenhuma, retorna vazio) e cria os que ainda não existem — casando a
    transportadora pelo CNPJ (comparado só pelos dígitos, já que o UNO manda sem pontuação
    e o nosso cadastro guarda formatado). Quando o CNPJ ainda não bate com nenhuma
    transportadora cadastrada, o romaneio é criado mesmo assim, em "definição da
    transportadora", pra KAMI atribuir manualmente (`aguardando_transportadora`) — no
    futuro, com o cadastro completo, isso deixa de acontecer. Duplicados (já importados)
    são reportados em `ignorados`, sem derrubar o restante do lote.
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

        comando = RomaneioCriarRequest(
            codigo=externo.codigo,
            transportadora_id=transportadora.id if transportadora else None,
            transportadora_cnpj_externo=None if transportadora else externo.transportadora_cnpj,
            qtd_caixas=externo.qtd_caixas,
            peso_total=externo.peso_total,
            tms_referencia_externa=externo.referencia_externa,
            tipo_veiculo_sugerido=externo.tipo_veiculo_sugerido,
            data_saida_prevista=externo.data_saida_prevista,
            empresa_nome=externo.empresa_nome,
            empresa_uf=externo.empresa_uf,
            pedidos=[_PedidoItem(**p.model_dump()) for p in externo.pedidos],
        )

        try:
            criar_de_comando(db, comando=comando, origem=OrigemRomaneio.UNO_REPLICA, usuario_atual=usuario_atual)
            if transportadora:
                resultado.importados.append(externo.codigo)
            else:
                resultado.aguardando_transportadora.append(externo.codigo)
        except RomaneioDuplicadoError:
            resultado.ignorados.append({"codigo": externo.codigo, "motivo": "já importado anteriormente"})

    resultado.reatribuidos = _reatribuir_transportadoras_pendentes(db, usuario_atual=usuario_atual)
    _backfill_empresa_romaneios_uno(db)

    return resultado


def _backfill_empresa_romaneios_uno(db: Session) -> int:
    """Preenche empresa_nome/empresa_uf de romaneios do UNO importados antes desse campo
    existir — não precisa reimportar (o que daria duplicado), só busca a empresa pela
    referência externa já salva e completa o que faltava."""
    from app.integrations.uno_source import get_romaneio_source

    sem_empresa = db.scalars(
        select(Romaneio).where(
            Romaneio.origem == OrigemRomaneio.UNO_REPLICA,
            Romaneio.empresa_nome.is_(None),
            Romaneio.tms_referencia_externa.isnot(None),
        )
    ).all()
    if not sem_empresa:
        return 0

    referencias = [r.tms_referencia_externa for r in sem_empresa]
    empresas_por_referencia = get_romaneio_source().buscar_empresas_por_referencia(referencias)

    atualizados = 0
    for romaneio in sem_empresa:
        dados = empresas_por_referencia.get(romaneio.tms_referencia_externa)
        if dados is None:
            continue
        romaneio.empresa_nome, romaneio.empresa_uf = dados
        atualizados += 1

    if atualizados:
        db.commit()
    return atualizados


def _reatribuir_transportadoras_pendentes(db: Session, *, usuario_atual: Usuario | None) -> list[str]:
    """Reavalia romaneios já importados que ficaram em 'definição da transportadora'
    (CNPJ não cadastrado na época) contra o cadastro atual de transportadoras — assim,
    cadastrar a transportadora depois já resolve o backlog sozinho, sem precisar reimportar
    o romaneio (que já existe e daria `RomaneioDuplicadoError` se tentássemos de novo)."""
    pendentes = db.scalars(
        select(Romaneio).where(Romaneio.status == StatusRomaneio.DEFINICAO_TRANSPORTADORA)
    ).all()
    if not pendentes:
        return []

    transportadoras_por_cnpj = {
        _somente_digitos(t.cnpj): t for t in db.scalars(select(Transportadora)).all()
    }

    reatribuidos = []
    for romaneio in pendentes:
        if not romaneio.transportadora_cnpj_externo:
            continue
        transportadora = transportadoras_por_cnpj.get(_somente_digitos(romaneio.transportadora_cnpj_externo))
        if transportadora is None:
            continue

        romaneio.transportadora_id = transportadora.id
        _transicionar(
            db, romaneio=romaneio, novo_status=StatusRomaneio.DEFINICAO_TRANSPORTE, usuario_atual=usuario_atual
        )
        reatribuidos.append(romaneio.codigo)

    if reatribuidos:
        db.commit()
    return reatribuidos


def definir_transportadora_inicial(
    db: Session, *, romaneio: Romaneio, transportadora_id: int, usuario_atual: Usuario
) -> Romaneio:
    """KAMI atribui a transportadora a um romaneio em 'definição da transportadora' (veio
    do UNO com CNPJ que ainda não batia com nenhum cadastro) — transiciona direto pra
    definição de transporte, como se já tivesse vindo casado desde o início."""
    if romaneio.status != StatusRomaneio.DEFINICAO_TRANSPORTADORA:
        raise TransicaoInvalidaError("Romaneio não está em definição da transportadora")

    transportadora = db.get(Transportadora, transportadora_id)
    if transportadora is None:
        raise TransportadoraInvalidaError("Transportadora informada não existe")

    romaneio.transportadora_id = transportadora_id
    _transicionar(
        db, romaneio=romaneio, novo_status=StatusRomaneio.DEFINICAO_TRANSPORTE, usuario_atual=usuario_atual
    )

    db.commit()
    db.refresh(romaneio)
    return romaneio
