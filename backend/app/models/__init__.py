"""Importa todos os models para que o Alembic (autogenerate) e Base.metadata os enxerguem."""

from app.models.evento_entrega import EventoEntrega
from app.models.foto_carregamento import FotoCarregamento
from app.models.historico_etapa import HistoricoEtapa
from app.models.log_auditoria import LogAuditoria
from app.models.motorista import Motorista
from app.models.pedido import Pedido
from app.models.resequenciamento import Resequenciamento
from app.models.romaneio import Romaneio
from app.models.tipo_ocorrencia import TipoOcorrencia
from app.models.transportadora import Transportadora
from app.models.usuario import PasswordResetToken, Usuario
from app.models.veiculo import Veiculo

__all__ = [
    "EventoEntrega",
    "FotoCarregamento",
    "HistoricoEtapa",
    "LogAuditoria",
    "Motorista",
    "Pedido",
    "Resequenciamento",
    "Romaneio",
    "TipoOcorrencia",
    "Transportadora",
    "PasswordResetToken",
    "Usuario",
    "Veiculo",
]
