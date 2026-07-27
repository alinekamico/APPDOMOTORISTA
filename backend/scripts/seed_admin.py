"""Cria o primeiro usuário kami_admin (bootstrap) — sem isso ninguém consegue logar.

Uso:
    python scripts/seed_admin.py --nome "Aline" --email aline@kamico.com.br --senha "TrocarDepois123!"

Reexecutar com o mesmo e-mail não duplica — atualiza a senha do usuário existente.
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.enums import Papel  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nome", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--senha", required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == args.email).one_or_none()
        if usuario:
            usuario.senha_hash = hash_password(args.senha)
            db.commit()
            print(f"Usuário {args.email} já existia — senha atualizada.")
            return

        usuario = Usuario(
            nome=args.nome,
            email=args.email,
            senha_hash=hash_password(args.senha),
            papel=Papel.KAMI_ADMIN,
            transportadora_id=None,
            departamento="Tecnologia da Informação",
        )
        db.add(usuario)
        db.commit()
        print(f"Usuário kami_admin criado: {args.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
