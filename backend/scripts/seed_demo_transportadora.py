"""Cria uma transportadora de demonstração completa: 1 login de transportadora_admin,
3 veículos, 3 motoristas com acesso já liberado, e 3 romaneios de exemplo com pedidos.

Uso:
    python scripts/seed_demo_transportadora.py

Reexecutar levanta erro de duplicado (CNPJ/placa/e-mail já existem) — apague os
registros no banco antes de rodar de novo, se precisar recriar.
"""

import secrets
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.enums import OrigemRomaneio, Papel  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402
from app.schemas.romaneio import PedidoCreateItem, RomaneioCriarRequest  # noqa: E402
from app.services import cadastro_service, romaneio_service  # noqa: E402


def gerar_senha() -> str:
    return secrets.token_urlsafe(9)


def main() -> None:
    db = SessionLocal()
    try:
        kami_admin = db.query(Usuario).filter(Usuario.papel == Papel.KAMI_ADMIN).first()
        if kami_admin is None:
            print("Nenhum kami_admin encontrado — rode scripts/seed_admin.py primeiro.")
            return

        credenciais: list[tuple[str, str, str]] = []

        transportadora = cadastro_service.criar_transportadora(
            db,
            razao_social="Expresso Demo Transportes Ltda",
            nome_fantasia="Expresso Demo",
            cnpj="12.345.678/0001-90",
            usuario_atual=kami_admin,
        )

        senha_admin = gerar_senha()
        cadastro_service.criar_admin_transportadora(
            db,
            transportadora_id=transportadora.id,
            nome="Admin Expresso Demo",
            email="admin@expressodemo.com.br",
            senha=senha_admin,
            departamento="Operações",
            usuario_atual=kami_admin,
        )
        credenciais.append(("Transportadora (transportadora_admin)", "admin@expressodemo.com.br", senha_admin))

        veiculos_dados = [
            ("DEM1A11", "Van", 1200.0),
            ("DEM2B22", "Caminhão VUC", 3000.0),
            ("DEM3C33", "Utilitário", 800.0),
        ]
        veiculos = []
        for placa, tipo, capacidade in veiculos_dados:
            v = cadastro_service.criar_veiculo(
                db,
                transportadora_id=transportadora.id,
                placa=placa,
                tipo=tipo,
                capacidade_kg=capacidade,
                usuario_atual=kami_admin,
            )
            veiculos.append(v)

        motoristas_dados = [
            ("Carlos Demo", "carlos.demo@expressodemo.com.br", "11999990001"),
            ("Fernanda Demo", "fernanda.demo@expressodemo.com.br", "11999990002"),
            ("Ricardo Demo", "ricardo.demo@expressodemo.com.br", "11999990003"),
        ]
        motoristas = []
        for nome, email, telefone in motoristas_dados:
            senha_motorista = gerar_senha()
            m = cadastro_service.criar_motorista(
                db,
                transportadora_id=transportadora.id,
                nome=nome,
                email=email,
                senha=senha_motorista,
                cnh=f"{secrets.randbelow(10**11):011d}",
                cnh_categoria="B",
                telefone=telefone,
                usuario_atual=kami_admin,
            )
            m.ativo = True
            m.usuario.ativo = True
            db.commit()
            db.refresh(m)
            motoristas.append(m)
            credenciais.append(("Motorista", email, senha_motorista))

        enderecos = [
            ("Farmácia Boa Saúde", "Av. Paulista, 1000 - Bela Vista, São Paulo - SP"),
            ("Mercado Central", "Rua Augusta, 500 - Consolação, São Paulo - SP"),
            ("Loja Vila Nova", "Av. Rebouças, 2000 - Pinheiros, São Paulo - SP"),
        ]

        for i in range(3):
            cliente_nome, cliente_endereco = enderecos[i]
            comando = RomaneioCriarRequest(
                codigo=f"RM-DEMO-{i + 1:03d}",
                transportadora_id=transportadora.id,
                tipo_veiculo_sugerido=veiculos[i].tipo,
                pedidos=[
                    PedidoCreateItem(
                        sequencia=1,
                        cliente_nome=cliente_nome,
                        cliente_endereco=cliente_endereco,
                        peso_kg=10.0 + i,
                        qtd_volumes=2 + i,
                        especie_volume="caixas",
                    )
                ],
            )
            romaneio_service.criar_de_comando(
                db, comando=comando, origem=OrigemRomaneio.MANUAL_TESTE, usuario_atual=kami_admin
            )

        print("\n=== Credenciais criadas ===")
        for papel, email, senha in credenciais:
            print(f"{papel}: {email} / {senha}")
        print("\n3 veículos, 3 motoristas (acesso já liberado) e 3 romaneios criados para 'Expresso Demo'.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
