#!/bin/sh
set -e

echo "Aguardando o MySQL ficar disponível..."
python - <<'PYEOF'
import time
import sys
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
connect_args = {"ssl": {"ca": settings.database_ssl_ca}} if settings.database_ssl_ca else {}
engine = create_engine(settings.database_url, connect_args=connect_args)

for tentativa in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("MySQL disponível.")
        sys.exit(0)
    except Exception:
        time.sleep(2)

print("MySQL não respondeu a tempo.", file=sys.stderr)
sys.exit(1)
PYEOF

echo "Rodando migrations..."
python -m alembic upgrade head

echo "Populando dados iniciais (idempotente)..."
python scripts/seed_admin.py \
    --nome "${ADMIN_NOME:-Aline}" \
    --email "${ADMIN_EMAIL:-aline@kamico.com.br}" \
    --senha "${ADMIN_SENHA:-TrocarDepois123!}"
python scripts/seed_tipos_ocorrencia.py

echo "Subindo a API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
