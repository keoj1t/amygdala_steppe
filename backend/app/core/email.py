import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings


class EmailClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def send_verification_code(self, recipient: str, code: str) -> None:
        subject = "AI Content Factory verification code"
        body = f"Your verification code is {code}. It expires in {self.settings.otp_expire_minutes} minutes."
        if not self.settings.smtp_host:
            print(f"Verification code for {recipient}: {code}")
            return
        await asyncio.to_thread(self._send_email, recipient, subject, body)

    def _send_email(self, recipient: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.settings.smtp_from_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_username and self.settings.smtp_password:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(message)
