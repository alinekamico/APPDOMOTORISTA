from typing import Protocol

Ponto = tuple[float, float]  # (lat, lng)


class DistanceMatrixProvider(Protocol):
    """Fornece a matriz de tempo estimado (minutos) de deslocamento entre pontos.

    `pontos[0]` é sempre a posição atual do motorista; os demais são as paradas pendentes.
    O heurístico de resequenciamento (nearest-neighbor + 2-opt) roda em cima do resultado
    desta função — trocar de provedor (Google, OSRM, etc.) não exige tocar no heurístico.
    """

    def obter_matriz_duracao(self, pontos: list[Ponto]) -> list[list[float]]: ...
