from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import OrigemRomaneio, StatusEntregaPedido, StatusRomaneio


class PedidoCreateItem(BaseModel):
    sequencia: int
    cliente_nome: str
    cliente_endereco: str
    cliente_lat: float | None = None
    cliente_lng: float | None = None
    cliente_whatsapp: str | None = None
    cliente_email: str | None = None
    # Logística — nunca valores monetários
    peso_kg: float | None = None
    qtd_volumes: int | None = None
    especie_volume: str | None = None
    dt_entrega_solicitada: date | None = None


class RomaneioCriarRequest(BaseModel):
    """Formato aceito tanto pelo webhook do TMS quanto pela tela manual de simulação."""

    codigo: str
    # None quando a fonte externa não conseguiu casar o CNPJ com uma transportadora
    # cadastrada — o romaneio entra em "definição da transportadora" pra KAMI atribuir.
    transportadora_id: int | None = None
    transportadora_cnpj_externo: str | None = None
    qtd_caixas: int | None = None
    peso_total: float | None = None
    tms_referencia_externa: str | None = None
    tipo_veiculo_sugerido: str | None = None
    data_saida_prevista: datetime | None = None
    empresa_nome: str | None = None
    empresa_uf: str | None = None
    # Ponto de partida pra roteirização automática (Regra 3): se informado e todos os pedidos
    # tiverem coordenadas, o sistema calcula a sequência de entrega sozinho (nearest-neighbor +
    # 2-opt) em vez de usar a ordem em que os pedidos foram digitados.
    origem_lat: float | None = None
    origem_lng: float | None = None
    pedidos: list[PedidoCreateItem]


class PedidoOut(BaseModel):
    id: int
    sequencia_original: int
    sequencia_atual: int
    status_entrega: StatusEntregaPedido
    cliente_nome: str
    cliente_endereco: str
    cliente_lat: float | None
    cliente_lng: float | None
    cliente_whatsapp: str | None
    cliente_email: str | None
    peso_kg: float | None
    qtd_volumes: int | None
    especie_volume: str | None
    dt_entrega_solicitada: date | None
    entregue_em: datetime | None

    model_config = {"from_attributes": True}


class FotoCarregamentoOut(BaseModel):
    id: int
    foto_url: str
    criado_em: datetime

    model_config = {"from_attributes": True}


class RomaneioOut(BaseModel):
    id: int
    codigo: str
    transportadora_id: int | None
    transportadora_nome: str | None
    transportadora_cnpj_externo: str | None = None
    veiculo_id: int | None
    veiculo_placa: str | None
    motorista_id: int | None
    motorista_nome: str | None
    status: StatusRomaneio
    origem: OrigemRomaneio
    qtd_caixas: int | None
    qtd_pedidos: int | None
    peso_total: float | None
    tipo_veiculo_sugerido: str | None = None
    data_saida_prevista: datetime | None = None
    empresa_nome: str | None = None
    empresa_uf: str | None = None
    fotos_carregamento: list[FotoCarregamentoOut] = []
    criado_em: datetime
    pedidos: list[PedidoOut] = []

    model_config = {"from_attributes": True}


class RomaneioResumoOut(BaseModel):
    """Versão sem a lista de pedidos, usada na listagem/kanban."""

    id: int
    codigo: str
    transportadora_id: int | None
    transportadora_nome: str | None
    transportadora_cnpj_externo: str | None = None
    veiculo_id: int | None
    veiculo_placa: str | None
    motorista_id: int | None
    motorista_nome: str | None
    status: StatusRomaneio
    qtd_caixas: int | None
    qtd_pedidos: int | None
    peso_total: float | None
    tipo_veiculo_sugerido: str | None = None
    data_saida_prevista: datetime | None = None
    empresa_nome: str | None = None
    empresa_uf: str | None = None
    criado_em: datetime

    model_config = {"from_attributes": True}


class AlterarTransportadoraRequest(BaseModel):
    transportadora_id: int


class DefinirTransportadoraRequest(BaseModel):
    """KAMI atribui a transportadora a um romaneio em 'definição da transportadora'
    (veio do UNO com CNPJ que ainda não bate com nenhum cadastro)."""

    transportadora_id: int


class DevolverParaTransporteRequest(BaseModel):
    observacao: str | None = None


class AlocarVeiculoMotoristaRequest(BaseModel):
    veiculo_id: int
    motorista_id: int


class InserirPedidosRequest(BaseModel):
    """Regra 7: adicionar parada(s) a um romaneio já em andamento."""

    pedidos: list[PedidoCreateItem]


class ResequenciarRequest(BaseModel):
    """Regra 4: motorista pede ajuste espontâneo da rota a partir da posição atual."""

    posicao_lat: float
    posicao_lng: float


class ReportarProblemaRequest(BaseModel):
    """Motorista aciona romaneio_incompleto ou romaneio_com_problema."""

    status: StatusRomaneio
    tipo_ocorrencia_id: int
    observacao: str
