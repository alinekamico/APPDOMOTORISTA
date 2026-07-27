import logging

from app.models.pedido import Pedido

logger = logging.getLogger("integrations.nps")


class StubCxNotifier:
    """Stub: apenas loga o disparo. A integração real (WhatsApp/SMS via provedor de CX) deve
    ser um serviço terceirizado, não construída internamente (ver pesquisa de mercado no plano).
    """

    def notify_delivery(self, pedido: Pedido) -> None:
        contato = pedido.cliente_whatsapp or pedido.cliente_email or "sem contato"
        logger.info("NPS (stub) — pedido_id=%s dispararia pesquisa para %s", pedido.id, contato)


def get_nps_notifier() -> StubCxNotifier:
    return StubCxNotifier()
