"""Inspeciona a réplica do UNO no Supabase: lista tabelas, colunas e mostra uma amostra
de linhas. Rode isso ANTES de editar `app/integrations/uno_source/supabase_adapter.py`,
pra saber os nomes reais de tabela/coluna em vez de adivinhar.

Uso:
    python scripts/inspect_uno_replica.py
    (lê UNO_REPLICA_DATABASE_URL do .env)

    python scripts/inspect_uno_replica.py "postgresql://usuario:senha@host:5432/postgres"
    (passa a connection string direto, sem precisar configurar o .env antes)
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, inspect, text  # noqa: E402

from app.core.config import get_settings  # noqa: E402


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else get_settings().uno_replica_database_url
    if not url:
        print("Faltou a connection string: passe como argumento ou configure UNO_REPLICA_DATABASE_URL no .env")
        sys.exit(1)

    engine = create_engine(url, pool_pre_ping=True)
    inspetor = inspect(engine)

    esquemas = [s for s in inspetor.get_schema_names() if s not in ("pg_catalog", "information_schema")]
    print(f"Esquemas encontrados: {esquemas}\n")

    for esquema in esquemas:
        tabelas = inspetor.get_table_names(schema=esquema)
        if not tabelas:
            continue
        print(f"=== esquema: {esquema} ===")
        for tabela in tabelas:
            print(f"\n[tabela] {esquema}.{tabela}")
            for coluna in inspetor.get_columns(tabela, schema=esquema):
                print(f"    {coluna['name']:<30} {coluna['type']}")

            with engine.connect() as conn:
                try:
                    amostra = conn.execute(text(f'SELECT * FROM "{esquema}"."{tabela}" LIMIT 3')).mappings().all()
                    if amostra:
                        print("    -- amostra --")
                        for linha in amostra:
                            print(f"    {dict(linha)}")
                except Exception as exc:
                    print(f"    (não consegui ler amostra: {exc})")


if __name__ == "__main__":
    main()
