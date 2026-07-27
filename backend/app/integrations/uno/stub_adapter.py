import logging

from app.models.enums import UnoSyncStatus
from app.models.evento_entrega import EventoEntrega

logger = logging.getLogger("integrations.uno")


class StubEvidenceSyncProvider:
    """Stub: apenas loga e marca como pendente — não há API/campo do UNO documentado ainda
    (Regra 5). Quando a integração real existir, plugar aqui um adapter que faça o POST/PUT
    de verdade e atualize `uno_sync_status` para SINCRONIZADO ou ERRO.
    """

    def sync(self, evento: EventoEntrega) -> None:
        logger.info("UNO sync (stub) — evento_entrega_id=%s permanece pendente", evento.id)
        evento.uno_sync_status = UnoSyncStatus.PENDENTE


def get_uno_provider() -> StubEvidenceSyncProvider:
    return StubEvidenceSyncProvider()
