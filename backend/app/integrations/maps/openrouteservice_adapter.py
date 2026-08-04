import httpx

from app.core.config import get_settings
from app.integrations.maps.interface import Ponto

# A OpenRouteService anunciou migração de api.openrouteservice.org para api.heigit.org, mas o
# path novo ainda não é um simples troca de domínio (retornou 404 no teste). Manter a URL
# atual, que segue funcionando, até a documentação da migração ficar clara.
MATRIX_URL = "https://api.openrouteservice.org/v2/matrix/driving-car"


class OpenRouteServiceDistanceMatrixProvider:
    """Usa a OpenRouteService (openrouteservice.org) — gratuita, sem cartão de crédito,
    chave criada só com e-mail. Alternativa ao Google Distance Matrix/Routes API.

    Limite do plano gratuito: matriz de até ~3500 rotas por requisição (N pontos, N² <= 3500,
    ou seja N <= ~59). Romaneios com mais paradas pendentes que isso no momento do recálculo
    vão falhar essa chamada — o chamador deve tratar isso como "sem otimização disponível
    agora" em vez de travar a entrega.
    """

    def __init__(self) -> None:
        self._api_key = get_settings().openrouteservice_api_key

    def obter_matriz_duracao(self, pontos: list[Ponto]) -> list[list[float]]:
        if not self._api_key:
            raise RuntimeError("OPENROUTESERVICE_API_KEY não configurada")

        locations = [[lng, lat] for lat, lng in pontos]  # ORS usa [lng, lat], ao contrário do nosso Ponto

        with httpx.Client(timeout=15.0) as client:
            resposta = client.post(
                MATRIX_URL,
                json={"locations": locations, "metrics": ["duration"]},
                headers={
                    "Authorization": self._api_key,
                    "Content-Type": "application/json; charset=utf-8",
                },
            )
            resposta.raise_for_status()
            dados = resposta.json()

        duracoes = dados.get("durations")
        if duracoes is None:
            raise RuntimeError(f"OpenRouteService não retornou 'durations': {dados}")

        return [[valor if valor is not None else float("inf") for valor in linha] for linha in duracoes]
