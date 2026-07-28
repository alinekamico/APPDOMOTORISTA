"""Busca romaneios na réplica do banco do UNO hospedada no Supabase (Postgres).

STATUS: validado contra dados reais (schema `unia`, permissão + RLS liberadas). Mapeamento
de tabelas confirmado:

  eq_romaneio_entrega          -> romaneio (cod_romaneio_entrega, cod_transportadora, cod_tp_veiculo, dt_saida)
  eq_romaneio_entrega_pedido   -> pedidos do romaneio (cod_pedido, ordem = sequência)
  vd_pedido                    -> dados do pedido/cliente (nome_cliente, telefone, email_cliente,
                                   latitude/longitude, peso_liquido/peso_bruto, qtd_volume, especie_volume,
                                   dt_entrega_solicitada) — tudo já vem aqui, sem precisar de join com cd_cliente
  vd_pedido_endereco           -> endereço estruturado do pedido (tp_endereco='E' = entrega, confirmado)
  cd_transportadora             -> cadastro da transportadora (cnpj, razao_social, nome_fantasia)
  cd_tipo_veiculo               -> descrição do tipo de veículo (cod_tp_veiculo)

Importante: a query NUNCA seleciona campos `vl_*`/`perc_*`/`aliquota_*` (valores monetários e
fiscais) — isso não deve ser exposto pra transportadora nem motorista. Só dados logísticos.

Mapeamento de `situacao` confirmado com a KAMI (romaneios de exemplo conferidos manualmente no UNO):
  10 = Aberto      (único status que deve ser importado pelo app)
  20 = Trânsito
  30 = Finalizado
  40 = Conferido

CNPJ é comparado só pelos dígitos (romaneio_service._somente_digitos) porque o UNO manda
sem pontuação.

Transportadora "teste"/"TESTE" no UNO é dado de teste/lixo (CNPJ de dígitos repetidos) —
excluída direto na query. Já "Retirada" (cliente retira no balcão) também usa CNPJ de
dígitos repetidos mas é um registro legítimo — tratada à parte em
cadastro_service.sincronizar_transportadoras_da_fonte_externa (NOME_RETIRADA).
"""

from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.integrations.uno_source.dto import PedidoExternoDTO, RomaneioExternoDTO, TransportadoraExternaDTO

QUERY_TRANSPORTADORAS = """
    SELECT
        t.cnpj,
        t.razao_social,
        t.nome_fantasia
    FROM unia.cd_transportadora t
    WHERE t.cnpj IS NOT NULL
"""

QUERY_EMPRESAS_POR_REFERENCIA = """
    SELECT
        r.cod_romaneio_entrega AS referencia_externa,
        e.nome_fantasia AS empresa_nome,
        e.sigla_uf AS empresa_uf
    FROM unia.eq_romaneio_entrega r
    LEFT JOIN unia.cd_empresa e ON e.cod_empresa = r.cod_empresa
    WHERE r.cod_romaneio_entrega = ANY(:referencias)
"""

QUERY_ROMANEIOS = """
    SELECT
        r.cod_romaneio_entrega AS referencia_externa,
        COALESCE(r.doc_romaneio::text, r.cod_romaneio_entrega::text) AS codigo,
        t.cnpj AS transportadora_cnpj,
        r.dt_saida AS data_saida_prevista,
        tv.descricao AS tipo_veiculo_sugerido,
        e.nome_fantasia AS empresa_nome,
        e.sigla_uf AS empresa_uf
    FROM unia.eq_romaneio_entrega r
    JOIN unia.cd_transportadora t ON t.cod_transportadora = r.cod_transportadora
    LEFT JOIN unia.cd_tipo_veiculo tv ON tv.cod_tp_veiculo = r.cod_tp_veiculo
    LEFT JOIN unia.cd_empresa e ON e.cod_empresa = r.cod_empresa
    WHERE r.situacao = 10
      AND lower(trim(t.nome_fantasia)) != 'teste'
    ORDER BY r.cod_romaneio_entrega DESC
"""

QUERY_PEDIDOS = """
    SELECT
        rp.ordem AS sequencia,
        p.nome_cliente AS cliente_nome,
        p.email_cliente AS cliente_email,
        NULLIF(p.ddd, '') || NULLIF(p.telefone, '') AS cliente_whatsapp,
        NULLIF(p.latitude, '')::float AS cliente_lat,
        NULLIF(p.longitude, '')::float AS cliente_lng,
        COALESCE(NULLIF(p.peso_bruto, 0), NULLIF(p.peso_liquido, 0)) AS peso_kg,
        p.qtd_volume AS qtd_volumes,
        p.especie_volume,
        p.dt_entrega_solicitada,
        pe.endereco, pe.numero, pe.bairro, pe.cidade, pe.sigla_uf, pe.cep
    FROM unia.eq_romaneio_entrega_pedido rp
    JOIN unia.vd_pedido p
        ON p.cod_pedido = rp.cod_pedido AND p.cod_empresa = rp.cod_empresa
    LEFT JOIN unia.vd_pedido_endereco pe
        ON pe.cod_pedido = p.cod_pedido AND pe.cod_empresa = p.cod_empresa AND pe.tp_endereco = 'E'
    WHERE rp.cod_romaneio_entrega = :cod_romaneio_entrega
    ORDER BY rp.ordem ASC
"""


def _montar_endereco(linha: dict) -> str:
    partes = [linha.get("endereco"), linha.get("numero"), linha.get("bairro"), linha.get("cidade"), linha.get("sigla_uf")]
    return ", ".join(p for p in partes if p) or "Endereço não informado"


class SupabaseUnoReplicaSource:
    """Conexão somente-leitura à réplica do UNO no Supabase. Nunca escreve nela."""

    def __init__(self) -> None:
        url = get_settings().uno_replica_database_url
        if not url:
            raise RuntimeError("UNO_REPLICA_DATABASE_URL não configurada")
        self._engine = create_engine(url, pool_pre_ping=True)

    def buscar_romaneios_pendentes(self) -> list[RomaneioExternoDTO]:
        with self._engine.connect() as conn:
            linhas_romaneio = conn.execute(text(QUERY_ROMANEIOS)).mappings().all()

            romaneios = []
            for linha in linhas_romaneio:
                linhas_pedido = conn.execute(
                    text(QUERY_PEDIDOS), {"cod_romaneio_entrega": linha["referencia_externa"]}
                ).mappings().all()

                pedidos = [
                    PedidoExternoDTO(
                        sequencia=p["sequencia"] or 0,
                        cliente_nome=p["cliente_nome"] or "Cliente sem nome",
                        cliente_endereco=_montar_endereco(dict(p)),
                        cliente_lat=p["cliente_lat"],
                        cliente_lng=p["cliente_lng"],
                        cliente_whatsapp=p["cliente_whatsapp"],
                        cliente_email=p["cliente_email"],
                        peso_kg=p["peso_kg"],
                        qtd_volumes=int(p["qtd_volumes"]) if p["qtd_volumes"] is not None else None,
                        especie_volume=p["especie_volume"],
                        dt_entrega_solicitada=p["dt_entrega_solicitada"],
                    )
                    for p in linhas_pedido
                ]

                romaneios.append(
                    RomaneioExternoDTO(
                        codigo=linha["codigo"],
                        transportadora_cnpj=linha["transportadora_cnpj"],
                        referencia_externa=str(linha["referencia_externa"]),
                        tipo_veiculo_sugerido=linha["tipo_veiculo_sugerido"],
                        data_saida_prevista=linha["data_saida_prevista"],
                        empresa_nome=linha["empresa_nome"],
                        empresa_uf=linha["empresa_uf"],
                        pedidos=pedidos,
                    )
                )
            return romaneios

    def buscar_transportadoras(self) -> list[TransportadoraExternaDTO]:
        with self._engine.connect() as conn:
            linhas = conn.execute(text(QUERY_TRANSPORTADORAS)).mappings().all()
            return [
                TransportadoraExternaDTO(
                    cnpj=linha["cnpj"],
                    razao_social=linha["razao_social"] or linha["nome_fantasia"] or linha["cnpj"],
                    nome_fantasia=linha["nome_fantasia"] or linha["razao_social"] or linha["cnpj"],
                )
                for linha in linhas
            ]

    def buscar_empresas_por_referencia(self, referencias: list[str]) -> dict[str, tuple[str, str | None]]:
        referencias_int = []
        for r in referencias:
            try:
                referencias_int.append(int(r))
            except (TypeError, ValueError):
                continue
        if not referencias_int:
            return {}

        with self._engine.connect() as conn:
            linhas = conn.execute(
                text(QUERY_EMPRESAS_POR_REFERENCIA), {"referencias": referencias_int}
            ).mappings().all()
            return {
                str(linha["referencia_externa"]): (linha["empresa_nome"], linha["empresa_uf"])
                for linha in linhas
                if linha["empresa_nome"]
            }
