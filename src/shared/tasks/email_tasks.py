import logging
from celery import shared_task
from src.shared.services.email import EmailService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, name="tasks.send_email")
def send_email(self, subject: str, to: str | list, text_body: str, html_body: str = None, from_email: str = None):
    """Generic async email task. Retries up to 3 times on failure (60 s delay)."""
    try:
        EmailService.send(subject, to, text_body, html_body, from_email)
    except Exception as exc:
        logger.exception("Failed to send email to %s (attempt %d/%d)", to, self.request.retries + 1, self.max_retries)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, name="tasks.send_password_reset_email")
def send_password_reset_email(self, to: str, name: str, code: str):
    """Send password-reset code email asynchronously."""
    try:
        EmailService.send_password_reset(to, name, code)
    except Exception as exc:
        logger.exception("Failed to send password reset email to %s", to)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, name="tasks.send_welcome_email")
def send_welcome_email(self, to: str, name: str):
    """Send welcome email after registration, asynchronously."""
    try:
        EmailService.send_welcome(to, name)
    except Exception as exc:
        logger.exception("Failed to send welcome email to %s", to)
        raise self.retry(exc=exc)
