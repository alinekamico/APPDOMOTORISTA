import httpx

from app.core.config import get_settings
from app.integrations.maps.interface import Ponto

DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


class GoogleDistanceMatrixProvider:
    """Usa a Google Distance Matrix API para tempo real de deslocamento (trânsito incluso).

    Só o tempo (duration) importa para o heurístico de resequenciamento — não pedimos
    otimização de rota à API do Google (isso seria o Route Optimization API, caro e
    desnecessário para o volume de paradas de um romaneio).
    """

    def __init__(self) -> None:
        self._api_key = get_settings().google_maps_api_key

    def obter_matriz_duracao(self, pontos: list[Ponto]) -> list[list[float]]:
        if not self._api_key:
            raise RuntimeError("GOOGLE_MAPS_API_KEY não configurada")

        locations = "|".join(f"{lat},{lng}" for lat, lng in pontos)
        params = {
            "origins": locations,
            "destinations": locations,
            "key": self._api_key,
            "departure_time": "now",
        }

        with httpx.Client(timeout=10.0) as client:
            resposta = client.get(DISTANCE_MATRIX_URL, params=params)
            resposta.raise_for_status()
            dados = resposta.json()

        if dados.get("status") != "OK":
            raise RuntimeError(f"Google Distance Matrix retornou status {dados.get('status')}")

        matriz: list[list[float]] = []
        for linha in dados["rows"]:
            linha_min = []
            for elemento in linha["elements"]:
                if elemento.get("status") != "OK":
                    linha_min.append(float("inf"))
                    continue
                duracao = elemento.get("duration_in_traffic") or elemento["duration"]
                linha_min.append(duracao["value"] / 60)
            matriz.append(linha_min)
        return matriz
