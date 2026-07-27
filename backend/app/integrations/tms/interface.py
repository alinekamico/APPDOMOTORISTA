from typing import Protocol

from app.schemas.romaneio import RomaneioCriarRequest


class TmsPayloadTranslator(Protocol):
    """Traduz o payload bruto que o TMS externo envia para o comando interno de criação de romaneio.

    Hoje o TMS real não existe/não está acessível — o `StubTmsPayloadTranslator` assume que o payload
    já chega no formato de `RomaneioCriarRequest`. Quando o TMS real for integrado, troca-se apenas
    a implementação (via `INTEGRATION_ADAPTER_TMS`), sem tocar em `romaneio_service`.
    """

    def to_romaneio_command(self, payload: dict) -> RomaneioCriarRequest: ...
