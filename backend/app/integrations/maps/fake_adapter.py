import math

from app.integrations.maps.interface import Ponto

VELOCIDADE_MEDIA_URBANA_KMH = 30.0


def _distancia_haversine_km(a: Ponto, b: Ponto) -> float:
    raio_terra_km = 6371.0
    lat1, lng1 = math.radians(a[0]), math.radians(a[1])
    lat2, lng2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlng = lat2 - lat1, lng2 - lng1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * raio_terra_km * math.asin(math.sqrt(h))


class FakeDistanceMatrixProvider:
    """Estima tempo de deslocamento por distância em linha reta (haversine) a uma velocidade
    urbana média — usado em dev/teste (`INTEGRATION_ADAPTER_MAPS=fake`) sem depender de API
    externa nem de chave do Google configurada.
    """

    def obter_matriz_duracao(self, pontos: list[Ponto]) -> list[list[float]]:
        return [
            [self._duracao_min(a, b) for b in pontos]
            for a in pontos
        ]

    def _duracao_min(self, a: Ponto, b: Ponto) -> float:
        if a == b:
            return 0.0
        distancia_km = _distancia_haversine_km(a, b)
        return (distancia_km / VELOCIDADE_MEDIA_URBANA_KMH) * 60
