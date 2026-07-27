from typing import Protocol

from app.models.evento_entrega import EventoEntrega


class EvidenceSyncProvider(Protocol):
    """Sincroniza evidências de entrega (foto/assinatura) com o sistema UNO.

    A evidência já foi gravada localmente (`eventos_entrega`) antes desta chamada — o UNO
    ainda não tem API/documentação acessível, então isso roda como fire-and-forget best-effort;
    falhas aqui nunca devem impedir o fluxo de entrega. `uno_sync_status` no evento permite
    reprocessar depois sem re-acoplar o fluxo de POD à disponibilidade do UNO.
    """

    def sync(self, evento: EventoEntrega) -> None: ...
