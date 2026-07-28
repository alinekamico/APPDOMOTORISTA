import asyncio
import logging

from app.db.session import SessionLocal
from app.services import romaneio_service

logger = logging.getLogger(__name__)

INTERVALO_SEGUNDOS = 600  # 10 minutos


async def sincronizar_uno_periodicamente() -> None:
    """Busca romaneios pendentes na fonte externa (réplica do UNO) a cada 10 minutos,
    sem depender de alguém clicar no botão de sincronização manual. Roda indefinidamente
    até a task ser cancelada no shutdown da aplicação."""
    while True:
        db = SessionLocal()
        try:
            resultado = romaneio_service.importar_de_fonte_externa(db, usuario_atual=None)
            if resultado.importados or resultado.ignorados:
                logger.info(
                    "Sincronização automática UNO: %d importados, %d ignorados",
                    len(resultado.importados),
                    len(resultado.ignorados),
                )
        except Exception:
            logger.exception("Falha na sincronização automática com a fonte externa de romaneios")
        finally:
            db.close()

        await asyncio.sleep(INTERVALO_SEGUNDOS)
