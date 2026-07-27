"""Popula o catálogo inicial de tipos_ocorrencia. Rode com: `python scripts/seed_tipos_ocorrencia.py`.

Reexecutar é seguro — pula códigos que já existem.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.enums import CategoriaOcorrencia  # noqa: E402
from app.models.tipo_ocorrencia import TipoOcorrencia  # noqa: E402

CATALOGO = [
    # Desvio de rota (Regra 1 — motorista pulou a sequência prevista)
    dict(categoria=CategoriaOcorrencia.DESVIO_ROTA, codigo="transito_intenso", descricao="Trânsito intenso na parada prevista", exige_foto=False, exige_observacao=False),
    dict(categoria=CategoriaOcorrencia.DESVIO_ROTA, codigo="cliente_solicitou_horario", descricao="Cliente solicitou outro horário", exige_foto=False, exige_observacao=True),
    dict(categoria=CategoriaOcorrencia.DESVIO_ROTA, codigo="otimizacao_proprio_motorista", descricao="Motorista otimizou a rota manualmente", exige_foto=False, exige_observacao=False),
    dict(categoria=CategoriaOcorrencia.DESVIO_ROTA, codigo="via_interditada", descricao="Via interditada ou bloqueada", exige_foto=False, exige_observacao=True),
    # Não entrega (pedido individual)
    dict(categoria=CategoriaOcorrencia.NAO_ENTREGA, codigo="cliente_ausente", descricao="Cliente ausente no endereço", exige_foto=False, exige_observacao=False),
    dict(categoria=CategoriaOcorrencia.NAO_ENTREGA, codigo="endereco_nao_localizado", descricao="Endereço não localizado", exige_foto=False, exige_observacao=True),
    dict(categoria=CategoriaOcorrencia.NAO_ENTREGA, codigo="recusa_cliente", descricao="Cliente recusou o recebimento", exige_foto=False, exige_observacao=True),
    dict(categoria=CategoriaOcorrencia.NAO_ENTREGA, codigo="avaria_produto", descricao="Avaria identificada no produto", exige_foto=True, exige_observacao=True),
    dict(categoria=CategoriaOcorrencia.NAO_ENTREGA, codigo="divergencia_pedido", descricao="Divergência entre pedido e carga", exige_foto=True, exige_observacao=True),
    # Problema no romaneio (romaneio_incompleto / romaneio_com_problema)
    dict(categoria=CategoriaOcorrencia.PROBLEMA_ROMANEIO, codigo="pane_mecanica", descricao="Pane mecânica no veículo", exige_foto=True, exige_observacao=True),
    dict(categoria=CategoriaOcorrencia.PROBLEMA_ROMANEIO, codigo="problema_saude_motorista", descricao="Problema de saúde do motorista", exige_foto=False, exige_observacao=True),
    dict(categoria=CategoriaOcorrencia.PROBLEMA_ROMANEIO, codigo="acidente", descricao="Acidente de trânsito", exige_foto=True, exige_observacao=True),
    dict(categoria=CategoriaOcorrencia.PROBLEMA_ROMANEIO, codigo="furto_roubo", descricao="Furto ou roubo da carga/veículo", exige_foto=False, exige_observacao=True),
]


def main() -> None:
    db = SessionLocal()
    try:
        existentes = {t.codigo for t in db.query(TipoOcorrencia).all()}
        novos = [TipoOcorrencia(**item) for item in CATALOGO if item["codigo"] not in existentes]
        db.add_all(novos)
        db.commit()
        print(f"{len(novos)} tipo(s) de ocorrência inserido(s). {len(existentes)} já existiam.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
