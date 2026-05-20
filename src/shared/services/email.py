from django.conf import settings
from django.core.mail import EmailMultiAlternatives


class EmailService:
    """
    Stateless email service. Use the static methods for common emails or
    call send() directly for custom messages.

    Designed to be framework-independent at the call site: views and tasks
    both call the same service; only the entry point differs (sync vs async).
    """

    @staticmethod
    def send(subject: str, to: str | list, text_body: str, html_body: str = None, from_email: str = None) -> None:
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        recipients = [to] if isinstance(to, str) else to
        msg = EmailMultiAlternatives(subject, text_body, from_email, recipients)
        if html_body:
            msg.attach_alternative(html_body, "text/html")
        msg.send()

    @staticmethod
    def send_password_reset(to: str, name: str, code: str) -> None:
        subject = "Password Reset Code"
        text = (
            f"Hello {name},\n\n"
            f"Your password reset code is: {code}\n\n"
            f"If you didn't request this, please ignore this email."
        )
        html = (
            f"<p>Hello <strong>{name}</strong>,</p>"
            f"<p>Your password reset code is:</p>"
            f"<h2 style='letter-spacing:4px'>{code}</h2>"
            f"<p>If you didn't request a password reset, you can safely ignore this email.</p>"
        )
        EmailService.send(subject, to, text, html)

    @staticmethod
    def send_welcome(to: str, name: str) -> None:
        subject = "Welcome!"
        text = f"Welcome {name}! Your account has been created successfully."
        html = (
            f"<h2>Welcome, {name}!</h2>"
            f"<p>Your account has been created successfully.</p>"
            f"<p>You can now log in and start using the platform.</p>"
        )
        EmailService.send(subject, to, text, html)
