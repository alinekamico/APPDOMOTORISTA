from datetime import date, datetime

from pydantic import BaseModel


class PedidoExternoDTO(BaseModel):
    """Um pedido/parada como vem da fonte externa (UNO), antes de virar `PedidoCreateItem`.

    Só campos logísticos — nenhum valor monetário é buscado da fonte externa (não deve ser
    exposto pra transportadora/motorista).
    """

    sequencia: int
    cliente_nome: str
    cliente_endereco: str
    cliente_lat: float | None = None
    cliente_lng: float | None = None
    cliente_whatsapp: str | None = None
    cliente_email: str | None = None
    peso_kg: float | None = None
    qtd_volumes: int | None = None
    especie_volume: str | None = None
    dt_entrega_solicitada: date | None = None


class TransportadoraExternaDTO(BaseModel):
    """Cadastro de transportadora como vem da fonte externa (UNO)."""

    cnpj: str
    razao_social: str
    nome_fantasia: str


class RomaneioExternoDTO(BaseModel):
    """Um romaneio como vem da fonte externa (UNO). Usa `transportadora_cnpj` (chave de
    negócio) em vez de `transportadora_id` porque o UNO não conhece nosso ID interno —
    quem resolve CNPJ → transportadora_id é `romaneio_service.importar_de_fonte_externa`.
    """

    codigo: str
    transportadora_cnpj: str
    referencia_externa: str | None = None
    qtd_caixas: int | None = None
    peso_total: float | None = None
    tipo_veiculo_sugerido: str | None = None
    data_saida_prevista: datetime | None = None
    # De qual empresa (dentro do grupo KAMI, no UNO) esse romaneio saiu — o UNO tem 30+
    # empresas cadastradas, então mostrar nome + UF ajuda a identificar de longe.
    empresa_nome: str | None = None
    empresa_uf: str | None = None
    pedidos: list[PedidoExternoDTO]
