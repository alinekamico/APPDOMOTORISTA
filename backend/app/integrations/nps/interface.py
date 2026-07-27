from typing import Protocol

from app.models.pedido import Pedido


class CxNotifier(Protocol):
    """Dispara a pesquisa de NPS/CSAT ao cliente final logo após a confirmação de entrega.

    Disparado por evento de domínio, depois que `eventos_entrega` já foi gravado com sucesso —
    nunca deve bloquear ou falhar o fluxo de POD. Implementação real (WhatsApp/SMS via provedor
    de CX) plugada depois via `INTEGRATION_ADAPTER_NPS`, sem tocar em `pod_service`.
    """

    def notify_delivery(self, pedido: Pedido) -> None: ...
