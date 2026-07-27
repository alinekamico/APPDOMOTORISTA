import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

settings = get_settings()


def enviar_email_redefinicao_senha(*, destinatario: str, nome: str, token: str) -> None:
    link = f"{settings.app_base_url}/redefinir-senha/{token}"
    corpo = (
        f"Olá, {nome},\n\n"
        "Recebemos uma solicitação para redefinir sua senha no sistema de romaneios da KAMI CO.\n"
        f"Clique no link abaixo para criar uma nova senha (válido por {settings.password_reset_expire_minutes} minutos):\n\n"
        f"{link}\n\n"
        "Se você não solicitou isso, ignore este e-mail.\n"
    )

    msg = EmailMessage()
    msg["Subject"] = "Redefinição de senha — KAMI CO."
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_user}>"
    msg["To"] = destinatario
    msg.set_content(corpo)

    if not settings.smtp_user or not settings.smtp_password:
        # Ambiente de desenvolvimento sem SMTP configurado: não falhar o fluxo, só não enviar de fato.
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
