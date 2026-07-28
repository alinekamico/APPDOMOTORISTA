from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import AcaoAuditoria, Papel
from app.models.motorista import Motorista
from app.models.transportadora import Transportadora
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.services import auditoria_service


class RegistroDuplicadoError(Exception):
    pass


def _somente_digitos(valor: str) -> str:
    return "".join(ch for ch in valor if ch.isdigit())


def _formatar_cnpj(digitos: str) -> str:
    if len(digitos) != 14:
        return digitos
    return f"{digitos[0:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:14]}"


# --- Transportadoras -------------------------------------------------------


def criar_transportadora(
    db: Session, *, razao_social: str, nome_fantasia: str, cnpj: str, usuario_atual: Usuario
) -> Transportadora:
    if db.scalar(select(Transportadora).where(Transportadora.cnpj == cnpj)):
        raise RegistroDuplicadoError("Já existe uma transportadora com este CNPJ")

    transportadora = Transportadora(razao_social=razao_social, nome_fantasia=nome_fantasia, cnpj=cnpj)
    db.add(transportadora)
    db.flush()

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="transportadoras",
        entidade_id=transportadora.id,
        acao=AcaoAuditoria.CREATE,
        dados_depois={"razao_social": razao_social, "nome_fantasia": nome_fantasia, "cnpj": cnpj},
    )
    db.commit()
    db.refresh(transportadora)
    return transportadora


NOME_RETIRADA = "retirada"


def _cnpj_valido(digitos: str) -> bool:
    """Descarta CNPJs claramente inválidos/de teste (todos os dígitos iguais, ex:
    '00000000000000' ou '11111111111111') — regra padrão de validação de CNPJ."""
    return bool(digitos) and len(set(digitos)) > 1


def sincronizar_transportadoras_da_fonte_externa(db: Session, *, usuario_atual: Usuario) -> dict:
    """Busca todas as transportadoras cadastradas na fonte externa (réplica do UNO) e
    cadastra na nossa base as que ainda não existem (casadas por CNPJ, só dígitos) — pra
    reduzir a fila de romaneios presos em "definição da transportadora" por falta de cadastro.
    Descarta registros de teste/inválidos (CNPJ com todos os dígitos iguais, nome "teste")."""
    from app.integrations.uno_source import get_romaneio_source

    externas = get_romaneio_source().buscar_transportadoras()

    existentes_por_cnpj = {_somente_digitos(t.cnpj) for t in db.scalars(select(Transportadora)).all()}

    criadas: list[str] = []
    ja_existentes: list[str] = []
    descartadas: list[str] = []
    vistas: set[str] = set()

    for externa in externas:
        digitos = _somente_digitos(externa.cnpj)
        if not digitos or digitos in vistas:
            continue
        vistas.add(digitos)

        nome_normalizado = externa.nome_fantasia.strip().lower()
        # "Retirada" (cliente retira no balcão, sem transportadora de verdade) usa um CNPJ
        # de dígitos repetidos no UNO, mas é um registro legítimo e recorrente — não é lixo/teste.
        if nome_normalizado == "teste" or (not _cnpj_valido(digitos) and nome_normalizado != NOME_RETIRADA):
            descartadas.append(externa.nome_fantasia)
            continue

        if digitos in existentes_por_cnpj:
            ja_existentes.append(externa.nome_fantasia)
            continue

        transportadora = Transportadora(
            razao_social=externa.razao_social,
            nome_fantasia=externa.nome_fantasia,
            cnpj=_formatar_cnpj(digitos),
        )
        db.add(transportadora)
        db.flush()

        auditoria_service.registrar(
            db,
            usuario_id=usuario_atual.id,
            entidade="transportadoras",
            entidade_id=transportadora.id,
            acao=AcaoAuditoria.CREATE,
            dados_depois={
                "razao_social": externa.razao_social,
                "nome_fantasia": externa.nome_fantasia,
                "cnpj": transportadora.cnpj,
                "origem": "sincronizacao_uno",
            },
        )
        criadas.append(externa.nome_fantasia)
        existentes_por_cnpj.add(digitos)

    db.commit()
    return {"criadas": criadas, "ja_existentes": ja_existentes, "descartadas": descartadas}


def criar_admin_transportadora(
    db: Session,
    *,
    transportadora_id: int,
    nome: str,
    email: str,
    senha: str,
    departamento: str | None,
    usuario_atual: Usuario,
) -> Usuario:
    if db.scalar(select(Usuario).where(Usuario.email == email)):
        raise RegistroDuplicadoError("Já existe um usuário com este e-mail")

    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=hash_password(senha),
        papel=Papel.TRANSPORTADORA_ADMIN,
        transportadora_id=transportadora_id,
        departamento=departamento,
    )
    db.add(usuario)
    db.flush()

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="usuarios",
        entidade_id=usuario.id,
        acao=AcaoAuditoria.CREATE,
        dados_depois={"papel": Papel.TRANSPORTADORA_ADMIN.value, "transportadora_id": transportadora_id},
    )
    db.commit()
    db.refresh(usuario)
    return usuario


def criar_kami_admin(
    db: Session, *, nome: str, email: str, senha: str, departamento: str | None, usuario_atual: Usuario
) -> Usuario:
    if db.scalar(select(Usuario).where(Usuario.email == email)):
        raise RegistroDuplicadoError("Já existe um usuário com este e-mail")

    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=hash_password(senha),
        papel=Papel.KAMI_ADMIN,
        transportadora_id=None,
        departamento=departamento,
    )
    db.add(usuario)
    db.flush()

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="usuarios",
        entidade_id=usuario.id,
        acao=AcaoAuditoria.CREATE,
        dados_depois={"papel": Papel.KAMI_ADMIN.value, "email": email},
    )
    db.commit()
    db.refresh(usuario)
    return usuario


def resetar_senha_usuario(db: Session, *, usuario_alvo: Usuario, nova_senha: str, usuario_atual: Usuario) -> Usuario:
    """KAMI reseta a senha de qualquer usuário do sistema — governança: 'Admin ... reseta senhas'."""
    usuario_alvo.senha_hash = hash_password(nova_senha)

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="usuarios",
        entidade_id=usuario_alvo.id,
        acao=AcaoAuditoria.UPDATE,
        dados_depois={"senha": "***redefinida pelo admin KAMI***"},
    )
    db.commit()
    db.refresh(usuario_alvo)
    return usuario_alvo


# --- Veículos ----------------------------------------------------------------


def criar_veiculo(
    db: Session, *, transportadora_id: int, placa: str, tipo: str, capacidade_kg: float | None, usuario_atual: Usuario
) -> Veiculo:
    if db.scalar(select(Veiculo).where(Veiculo.placa == placa)):
        raise RegistroDuplicadoError("Já existe um veículo com esta placa")

    veiculo = Veiculo(transportadora_id=transportadora_id, placa=placa, tipo=tipo, capacidade_kg=capacidade_kg)
    db.add(veiculo)
    db.flush()

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="veiculos",
        entidade_id=veiculo.id,
        acao=AcaoAuditoria.CREATE,
        dados_depois={"placa": placa, "tipo": tipo, "transportadora_id": transportadora_id},
    )
    db.commit()
    db.refresh(veiculo)
    return veiculo


def atualizar_veiculo(
    db: Session, *, veiculo: Veiculo, tipo: str | None, capacidade_kg: float | None, ativo: bool | None, usuario_atual: Usuario
) -> Veiculo:
    dados_antes = {"tipo": veiculo.tipo, "capacidade_kg": veiculo.capacidade_kg, "ativo": veiculo.ativo}

    if tipo is not None:
        veiculo.tipo = tipo
    if capacidade_kg is not None:
        veiculo.capacidade_kg = capacidade_kg
    if ativo is not None:
        veiculo.ativo = ativo

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="veiculos",
        entidade_id=veiculo.id,
        acao=AcaoAuditoria.UPDATE,
        dados_antes=dados_antes,
        dados_depois={"tipo": veiculo.tipo, "capacidade_kg": float(veiculo.capacidade_kg) if veiculo.capacidade_kg else None, "ativo": veiculo.ativo},
    )
    db.commit()
    db.refresh(veiculo)
    return veiculo


# --- Motoristas ----------------------------------------------------------------


def criar_motorista(
    db: Session,
    *,
    transportadora_id: int,
    nome: str,
    email: str,
    senha: str,
    cnh: str,
    cnh_categoria: str,
    telefone: str,
    usuario_atual: Usuario,
) -> Motorista:
    if db.scalar(select(Usuario).where(Usuario.email == email)):
        raise RegistroDuplicadoError("Já existe um usuário com este e-mail")

    # Motorista é, ao mesmo tempo, um cadastro de usuário do sistema da transportadora — mas
    # começa SEM acesso liberado. A transportadora decide quando liberar (PATCH /motoristas/{id}
    # com ativo=true), separando "cadastrar o motorista" de "dar acesso ao app pra ele".
    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=hash_password(senha),
        papel=Papel.MOTORISTA,
        transportadora_id=transportadora_id,
        ativo=False,
    )
    db.add(usuario)
    db.flush()

    motorista = Motorista(
        usuario_id=usuario.id,
        transportadora_id=transportadora_id,
        cnh=cnh,
        cnh_categoria=cnh_categoria,
        telefone=telefone,
        ativo=False,
    )
    db.add(motorista)
    db.flush()

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="motoristas",
        entidade_id=motorista.id,
        acao=AcaoAuditoria.CREATE,
        dados_depois={"nome": nome, "email": email, "transportadora_id": transportadora_id},
    )
    db.commit()
    db.refresh(motorista)
    return motorista


def atualizar_motorista(
    db: Session,
    *,
    motorista: Motorista,
    telefone: str | None,
    ativo: bool | None,
    senha: str | None,
    usuario_atual: Usuario,
) -> Motorista:
    dados_antes = {"telefone": motorista.telefone, "ativo": motorista.ativo}

    if telefone is not None:
        motorista.telefone = telefone
    if ativo is not None:
        motorista.ativo = ativo
        motorista.usuario.ativo = ativo
    if senha is not None:
        motorista.usuario.senha_hash = hash_password(senha)

    dados_depois = {"telefone": motorista.telefone, "ativo": motorista.ativo}
    if senha is not None:
        dados_depois["senha"] = "***alterada pela transportadora***"

    auditoria_service.registrar(
        db,
        usuario_id=usuario_atual.id,
        entidade="motoristas",
        entidade_id=motorista.id,
        acao=AcaoAuditoria.UPDATE,
        dados_antes=dados_antes,
        dados_depois=dados_depois,
    )
    db.commit()
    db.refresh(motorista)
    return motorista
