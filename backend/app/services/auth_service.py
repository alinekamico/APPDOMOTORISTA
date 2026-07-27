from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    generate_reset_token,
    hash_password,
    verify_password,
    verify_reset_token,
)
from app.models.enums import AcaoAuditoria
from app.models.usuario import PasswordResetToken, Usuario
from app.services import auditoria_service
from app.services.email_service import enviar_email_redefinicao_senha

settings = get_settings()


class CredenciaisInvalidasError(Exception):
    pass


def autenticar(db: Session, *, email: str, senha: str, ip: str | None, user_agent: str | None) -> tuple[Usuario, str]:
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))

    if usuario is None or not usuario.ativo or not verify_password(senha, usuario.senha_hash):
        auditoria_service.registrar(
            db,
            usuario_id=usuario.id if usuario else None,
            entidade="usuarios",
            entidade_id=usuario.id if usuario else None,
            acao=AcaoAuditoria.LOGIN_FAILED,
            ip=ip,
            user_agent=user_agent,
        )
        db.commit()
        raise CredenciaisInvalidasError("E-mail ou senha inválidos")

    usuario.last_login_at = datetime.now(timezone.utc)
    auditoria_service.registrar(
        db,
        usuario_id=usuario.id,
        entidade="usuarios",
        entidade_id=usuario.id,
        acao=AcaoAuditoria.LOGIN,
        ip=ip,
        user_agent=user_agent,
    )
    db.commit()

    token = create_access_token(
        subject=str(usuario.id), papel=usuario.papel.value, transportadora_id=usuario.transportadora_id
    )
    return usuario, token


def solicitar_redefinicao_senha(db: Session, *, email: str) -> None:
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    if usuario is None or not usuario.ativo:
        # Não revelar se o e-mail existe ou não.
        return

    raw_token, token_hash = generate_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_expire_minutes)

    reset_token = PasswordResetToken(usuario_id=usuario.id, token_hash=token_hash, expires_at=expires_at)
    db.add(reset_token)
    db.commit()

    enviar_email_redefinicao_senha(destinatario=usuario.email, nome=usuario.nome, token=raw_token)


def redefinir_senha(db: Session, *, raw_token: str, nova_senha: str) -> None:
    candidatos = db.scalars(
        select(PasswordResetToken)
        .where(PasswordResetToken.used_at.is_(None))
        .order_by(PasswordResetToken.criado_em.desc())
    ).all()

    agora = datetime.now(timezone.utc)
    for candidato in candidatos:
        expires_at = candidato.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < agora:
            continue
        if verify_reset_token(raw_token, candidato.token_hash):
            usuario = db.get(Usuario, candidato.usuario_id)
            if usuario is None:
                raise ValueError("Token inválido")
            usuario.senha_hash = hash_password(nova_senha)
            candidato.used_at = agora
            db.commit()
            return

    raise ValueError("Token inválido ou expirado")
