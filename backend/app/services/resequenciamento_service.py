from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.maps import get_maps_provider
from app.integrations.maps.interface import Ponto
from app.models.enums import OrigemResequenciamento, StatusEntregaPedido
from app.models.pedido import Pedido
from app.models.resequenciamento import Resequenciamento
from app.models.romaneio import Romaneio
from app.models.usuario import Usuario
from app.services import auditoria_service
from app.models.enums import AcaoAuditoria


class JustificativaObrigatoriaError(Exception):
    pass


class SemCoordenadasError(Exception):
    pass


def calcular_sequencia_otima(matriz_duracao: list[list[float]]) -> list[int]:
    """Heurístico puro (sem I/O): nearest-neighbor + 2-opt sobre uma matriz de tempo (minutos).

    `matriz_duracao[0]` é sempre a posição atual do motorista. Retorna a ordem de visita dos
    demais pontos como índices 1..N-1 (relativos à matriz de entrada), do primeiro ao último.
    """
    n = len(matriz_duracao)
    if n <= 1:
        return []
    if n == 2:
        return [1]

    # --- construção: nearest-neighbor a partir do ponto 0 ---
    nao_visitados = set(range(1, n))
    rota = []
    atual = 0
    while nao_visitados:
        proximo = min(nao_visitados, key=lambda i: matriz_duracao[atual][i])
        rota.append(proximo)
        nao_visitados.remove(proximo)
        atual = proximo

    # --- melhoria: 2-opt sobre o caminho aberto (0 -> rota[0] -> ... -> rota[-1]) ---
    def custo_total(caminho: list[int]) -> float:
        pontos = [0, *caminho]
        return sum(matriz_duracao[pontos[i]][pontos[i + 1]] for i in range(len(pontos) - 1))

    melhorou = True
    while melhorou:
        melhorou = False
        for i in range(len(rota) - 1):
            for j in range(i + 1, len(rota)):
                candidata = rota[: i] + rota[i : j + 1][::-1] + rota[j + 1 :]
                if custo_total(candidata) < custo_total(rota) - 1e-9:
                    rota = candidata
                    melhorou = True

    return rota


def _registrar_resequenciamento(
    db: Session,
    *,
    romaneio: Romaneio,
    usuario_atual: Usuario,
    origem: OrigemResequenciamento,
    sequencia_antes: list[dict],
    pendentes_depois: list[Pedido],
    tipo_ocorrencia_id: int | None,
    observacao: str | None,
    tempo_estimado_min: float | None,
) -> None:
    resequenciamento = Resequenciamento(
        romaneio_id=romaneio.id,
        usuario_id=usuario_atual.id,
        origem=origem,
        sequencia_antes=sequencia_antes,
        sequencia_depois=[{"pedido_id": p.id, "sequencia": p.sequencia_atual} for p in pendentes_depois],
        tipo_ocorrencia_id=tipo_ocorrencia_id,
        observacao=observacao,
        tempo_estimado_min=tempo_estimado_min,
    )
    db.add(resequenciamento)

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="romaneios",
        entidade_id=romaneio.id,
        acao=AcaoAuditoria.RESEQUENCIAMENTO,
        dados_antes={"sequencia": resequenciamento.sequencia_antes},
        dados_depois={"sequencia": resequenciamento.sequencia_depois},
    )


def resequenciar_pendentes(
    db: Session,
    *,
    romaneio: Romaneio,
    usuario_atual: Usuario,
    origem: OrigemResequenciamento,
    posicao_atual: Ponto | None,
    tipo_ocorrencia_id: int | None = None,
    observacao: str | None = None,
) -> Romaneio:
    """Recalcula a ordem dos pedidos ainda pendentes (Regras 1, 4 e 7).

    Regra 1 exige `tipo_ocorrencia_id` quando `origem == DIVERGENCIA_MANUAL`. As demais origens
    (ajuste espontâneo do motorista, inserção de novo pedido) não exigem justificativa.
    """
    if origem == OrigemResequenciamento.DIVERGENCIA_MANUAL and tipo_ocorrencia_id is None:
        raise JustificativaObrigatoriaError("É necessário justificar o motivo do desvio de sequência")

    pendentes = sorted(
        (p for p in romaneio.pedidos if p.status_entrega in {StatusEntregaPedido.PENDENTE, StatusEntregaPedido.EM_ROTA}),
        key=lambda p: p.sequencia_atual,
    )
    if len(pendentes) <= 1:
        return romaneio

    pendentes_com_coordenadas = [p for p in pendentes if p.cliente_lat is not None and p.cliente_lng is not None]
    if len(pendentes_com_coordenadas) != len(pendentes) or posicao_atual is None:
        raise SemCoordenadasError(
            "Não é possível recalcular a rota sem a localização atual e o endereço geocodificado de todas as paradas pendentes"
        )

    sequencia_antes = [{"pedido_id": p.id, "sequencia": p.sequencia_atual} for p in pendentes]

    pontos: list[Ponto] = [posicao_atual] + [(float(p.cliente_lat), float(p.cliente_lng)) for p in pendentes]
    matriz = get_maps_provider().obter_matriz_duracao(pontos)
    ordem = calcular_sequencia_otima(matriz)  # índices 1..N relativos a `pontos`/`pendentes`

    tempo_total_min = sum(matriz[a][b] for a, b in zip([0, *ordem], ordem))

    # Renumera TODO o romaneio (não só os pendentes) pra manter sempre uma sequência 1..N
    # contígua, sem lacunas nem números além do total de pedidos. Entregas fora de ordem (ex:
    # entregou o 1 e o 4, pulando 2 e 3) deixavam "buracos" que inflavam a sequência dos
    # pendentes pra além de N (ex: virava 5..13 num romaneio de 11 pedidos) — confuso na tela
    # e no mapa. Pedidos já finalizados mantêm a ordem relativa entre si, só compactada.
    finalizados_ordenados = sorted(
        (p for p in romaneio.pedidos if p not in pendentes), key=lambda p: p.sequencia_atual
    )
    for posicao, pedido in enumerate(finalizados_ordenados, start=1):
        pedido.sequencia_atual = posicao

    proxima_sequencia = len(finalizados_ordenados) + 1
    for posicao, indice_pendente in enumerate(ordem):
        pedido = pendentes[indice_pendente - 1]
        pedido.sequencia_atual = proxima_sequencia + posicao

    _registrar_resequenciamento(
        db,
        romaneio=romaneio,
        usuario_atual=usuario_atual,
        origem=origem,
        sequencia_antes=sequencia_antes,
        pendentes_depois=pendentes,
        tipo_ocorrencia_id=tipo_ocorrencia_id,
        observacao=observacao,
        tempo_estimado_min=tempo_total_min,
    )

    db.commit()
    db.refresh(romaneio)
    return romaneio
