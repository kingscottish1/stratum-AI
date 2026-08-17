"""
Email sending (SMTP) with HTML template support.

Env vars: SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional


class EmailHandler:
    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.from_addr = os.getenv("EMAIL_FROM", self.username)

    def send(
        self,
        to: str,
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
        cc: Optional[list[str]] = None,
    ) -> dict:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = to
        if cc:
            msg["Cc"] = ", ".join(cc)

        if text:
            msg.attach(MIMEText(text, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))

        recipients = [to] + (cc or [])
        with smtplib.SMTP(self.host, self.port, timeout=30) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.from_addr, recipients, msg.as_string())
        return {"to": to, "subject": subject, "status": "sent"}

    def send_template(self, to: str, subject: str, template_path: str, **kwargs) -> dict:
        """Render an HTML template file and send it."""
        with open(template_path, "r", encoding="utf-8") as fh:
            html = fh.read()
        for key, value in kwargs.items():
            html = html.replace("{{" + key + "}}", str(value))
        return self.send(to, subject, html=html)
