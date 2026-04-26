# app/services/email_service.py
import smtplib
import secrets
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings


class EmailService:
    @staticmethod
    def generate_verification_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_verification_email(email: str, token: str) -> MIMEMultipart:
        settings = get_settings()
        verify_url = f"{settings.app_url}/auth/verify-email?token={token}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Подтвердите ваш email"
        msg["From"] = settings.smtp_from_email
        msg["To"] = email

        text = f"""
Добро пожаловать!

Для подтверждения email перейдите по ссылке:
{verify_url}

Ссылка действительна {settings.verification_token_expire_hours} часов.
Если вы не регистрировались, просто проигнорируйте это письмо.
"""

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 500px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .header {{ background: #3B82F6; padding: 30px; text-align: center; }}
        .header h1 {{ color: #fff; margin: 0; font-size: 24px; }}
        .content {{ padding: 30px; }}
        .content p {{ color: #374151; line-height: 1.6; margin: 0 0 20px; }}
        .button {{ display: inline-block; background: #3B82F6; color: #fff; text-decoration: none; padding: 12px 32px; border-radius: 8px; font-weight: 600; }}
        .button:hover {{ background: #2563EB; }}
        .footer {{ background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }}
        .link-text {{ word-break: break-all; color: #3B82F6; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Подтвердите email</h1>
        </div>
        <div class="content">
            <p>Добро пожаловать! Для активации аккаунта подтвердите ваш email.</p>
            <p style="text-align: center;">
                <a href="{verify_url}" class="button">Подтвердить email</a>
            </p>
            <p>Или перейдите по ссылке:</p>
            <p class="link-text">{verify_url}</p>
            <p>Ссылка действительна <strong>{settings.verification_token_expire_hours} часов</strong>.</p>
            <p style="color: #9ca3af; font-size: 14px;">Если вы не регистрировались, проигнорируйте это письмо.</p>
        </div>
        <div class="footer">
            SecureAuth &copy; {datetime.now().year}
        </div>
    </div>
</body>
</html>
"""

        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
        return msg

    def send_verification_email(self, email: str, token: str) -> bool:
        settings = get_settings()
        msg = self.create_verification_email(email, token)

        if not settings.smtp_user or not settings.smtp_password:
            print(f"⚠️ SMTP не настроен. Токен верификации: {token}")
            print(f"🔗 Ссылка для верификации: {settings.app_url}/auth/verify-email?token={token}")
            return True

        try:
            if settings.smtp_use_tls:
                server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)

            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки email: {e}")
            return False


email_service = EmailService()
