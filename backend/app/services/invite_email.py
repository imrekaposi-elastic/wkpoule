import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings

logger = logging.getLogger(__name__)


def send_subgroup_invite_email(
    to_email: str,
    subgroup_name: str,
    inviter_username: str,
) -> None:
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_from:
        logger.info("SMTP not configured; skipping invite email to %s", to_email)
        return

    link = f"{settings.public_app_url.rstrip('/')}/subgroups"
    body = (
        f"You were invited by {inviter_username} to join the Worldcup 2026 game subgroup «{subgroup_name}».\n\n"
        f"Open the app and sign in with this email address, then go to Subgroup to accept the invitation:\n"
        f"{link}\n"
    )
    msg = EmailMessage()
    msg["Subject"] = f"Invitation: {subgroup_name} (Worldcup 2026 game)"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(body)

    try:
        if settings.smtp_use_tls:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
                smtp.starttls()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(msg)
    except Exception:
        logger.exception("Failed to send invite email to %s", to_email)
