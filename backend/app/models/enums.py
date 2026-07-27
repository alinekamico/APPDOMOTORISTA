import enum


class Papel(str, enum.Enum):
    KAMI_ADMIN = "kami_admin"
    TRANSPORTADORA_ADMIN = "transportadora_admin"
    MOTORISTA = "motorista"


class StatusRomaneio(str, enum.Enum):
    DEFINICAO_TRANSPORTE = "definicao_transporte"
    CONFERENCIA_LOGISTICA = "conferencia_logistica"
    CARREGAMENTO = "carregamento"
    INICIO_ROTA = "inicio_rota"
    EM_TRANSITO = "em_transito"
    CONCLUIDO = "concluido"
    ROMANEIO_INCOMPLETO = "romaneio_incompleto"
    ROMANEIO_COM_PROBLEMA = "romaneio_com_problema"


class OrigemRomaneio(str, enum.Enum):
    WEBHOOK_TMS = "webhook_tms"
    MANUAL_TESTE = "manual_teste"
    UNO_REPLICA = "uno_replica"


class StatusEntregaPedido(str, enum.Enum):
    PENDENTE = "pendente"
    EM_ROTA = "em_rota"
    ENTREGUE = "entregue"
    NAO_ENTREGUE = "nao_entregue"
    CANCELADO = "cancelado"


class CategoriaOcorrencia(str, enum.Enum):
    DESVIO_ROTA = "desvio_rota"
    NAO_ENTREGA = "nao_entrega"
    PROBLEMA_ROMANEIO = "problema_romaneio"


class TipoEventoEntrega(str, enum.Enum):
    ENTREGUE = "entregue"
    NAO_ENTREGUE = "nao_entregue"


class UnoSyncStatus(str, enum.Enum):
    PENDENTE = "pendente"
    SINCRONIZADO = "sincronizado"
    ERRO = "erro"


class OrigemResequenciamento(str, enum.Enum):
    DIVERGENCIA_MANUAL = "divergencia_manual"
    INSERCAO_PEDIDO = "insercao_pedido"
    AJUSTE_ESPONTANEO = "ajuste_espontaneo"


class AcaoAuditoria(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    TRANSICAO_ETAPA = "transicao_etapa"
    RESEQUENCIAMENTO = "resequenciamento"
