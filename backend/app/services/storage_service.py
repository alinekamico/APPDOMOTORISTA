import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings

settings = get_settings()


def salvar_arquivo(upload: UploadFile, *, subpasta: str) -> str:
    """Salva localmente (disco) e retorna a URL relativa (`/uploads/...`).

    Em produção isso troca para S3 sem alterar quem chama esta função — mantém o storage
    isolado atrás de uma única função, mesmo sem uma interface Protocol formal (o volume de
    uso ainda não justifica a abstração completa como nos adapters de integração externa).
    """
    pasta = Path(settings.upload_dir) / subpasta
    pasta.mkdir(parents=True, exist_ok=True)

    extensao = Path(upload.filename or "").suffix or ".bin"
    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
    destino = pasta / nome_arquivo

    with destino.open("wb") as f:
        f.write(upload.file.read())

    return f"/uploads/{subpasta}/{nome_arquivo}"
