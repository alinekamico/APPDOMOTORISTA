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
