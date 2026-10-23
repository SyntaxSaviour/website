"""
Email delivery service.

Sends two types of emails per enquiry:
  1. Internal notification to the BrainMint team (Ashutosh's business inbox).
  2. Acknowledgement to the enquirer.

Configuration (all in .env):
  EMAIL_PROVIDER   = smtp | sendgrid | mailgun  (default: smtp)
  SMTP_HOST        = smtp.example.com
  SMTP_PORT        = 587
  SMTP_USERNAME    = user@example.com
  SMTP_PASSWORD    = secret
  SMTP_USE_TLS     = true
  EMAIL_FROM       = BrainMint Software <hello@brainmint.com>
  EMAIL_TEAM_TO    = ashutosh@brainmint.com
  SENDGRID_API_KEY = SG.xxx   (if EMAIL_PROVIDER=sendgrid)
  MAILGUN_API_KEY  = key-xxx  (if EMAIL_PROVIDER=mailgun)
  MAILGUN_DOMAIN   = mg.brainmint.com
"""

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"


class EmailDeliveryError(Exception):
    """Raised when the email cannot be delivered after all retries."""


def _load_template(filename: str, context: dict) -> str:
    """Load an HTML template and do simple {key} substitution."""
    path = TEMPLATE_DIR / filename
    if not path.exists():
        logger.warning("Email template not found: %s", path)
        return ""
    content = path.read_text(encoding="utf-8")
    for key, value in context.items():
        content = content.replace(f"{{{{{key}}}}}", str(value or ""))
    return content


class EmailService:
    def __init__(self):
        self.provider: str = getattr(settings, "EMAIL_PROVIDER", "smtp")
        self.from_addr: str = getattr(
            settings, "EMAIL_FROM", "BrainMint Software <hello@brainmint.com>"
        )
        self.team_to: str = getattr(settings, "EMAIL_TEAM_TO", "")
        self.enabled: bool = bool(getattr(settings, "EMAIL_ENABLED", True))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_enquiry_notification(
        self,
        *,
        name: str,
        email: str,
        phone: Optional[str],
        service: Optional[str],
        message: str,
        source: str,
        enquiry_id: int,
    ) -> None:
        """Send the internal notification email to the BrainMint team."""
        if not self.team_to:
            logger.warning("EMAIL_TEAM_TO not configured – skipping team notification.")
            return

        context = {
            "name": name,
            "email": email,
            "phone": phone or "—",
            "service": service or "General Enquiry",
            "message": message,
            "source": source.replace("_", " ").title(),
            "enquiry_id": enquiry_id,
        }
        html_body = _load_template("enquiry_notification.html", context)
        subject = f"New Enquiry #{enquiry_id} from {name} – BrainMint"
        self._dispatch(to=self.team_to, subject=subject, html_body=html_body)

    def send_enquiry_acknowledgement(
        self,
        *,
        name: str,
        to_email: str,
        service: Optional[str],
    ) -> None:
        """Send the acknowledgement email to the enquirer."""
        context = {
            "name": name,
            "service": service or "your enquiry",
        }
        html_body = _load_template("enquiry_acknowledgement.html", context)
        subject = "We've received your enquiry – BrainMint Software"
        self._dispatch(to=to_email, subject=subject, html_body=html_body)

    # ------------------------------------------------------------------
    # Private dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, *, to: str, subject: str, html_body: str) -> None:
        if not self.enabled:
            logger.info("EMAIL_ENABLED=false – email not sent to %s", to)
            return

        if self.provider == "sendgrid":
            self._send_via_sendgrid(to=to, subject=subject, html_body=html_body)
        elif self.provider == "mailgun":
            self._send_via_mailgun(to=to, subject=subject, html_body=html_body)
        else:
            self._send_via_smtp(to=to, subject=subject, html_body=html_body)

    def _send_via_smtp(self, *, to: str, subject: str, html_body: str) -> None:
        host = getattr(settings, "SMTP_HOST", "")
        port = int(getattr(settings, "SMTP_PORT", 587))
        username = getattr(settings, "SMTP_USERNAME", "")
        password = getattr(settings, "SMTP_PASSWORD", "")
        use_tls = str(getattr(settings, "SMTP_USE_TLS", "true")).lower() == "true"

        if not host:
            logger.warning("SMTP_HOST not configured – cannot send email.")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            context = ssl.create_default_context() if use_tls else None
            with smtplib.SMTP(host, port, timeout=10) as server:
                if use_tls:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                if username and password:
                    server.login(username, password)
                server.sendmail(self.from_addr, to, msg.as_string())
            logger.info("Email sent via SMTP to %s | subject: %s", to, subject)
        except Exception as exc:
            logger.error("SMTP send failed to %s: %s", to, exc)
            raise EmailDeliveryError(str(exc)) from exc

    def _send_via_sendgrid(self, *, to: str, subject: str, html_body: str) -> None:
        try:
            import httpx

            api_key = getattr(settings, "SENDGRID_API_KEY", "")
            if not api_key:
                logger.warning("SENDGRID_API_KEY not set.")
                return

            payload = {
                "personalizations": [{"to": [{"email": to}]}],
                "from": {"email": self.from_addr},
                "subject": subject,
                "content": [{"type": "text/html", "value": html_body}],
            }
            resp = httpx.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0,
            )
            resp.raise_for_status()
            logger.info("Email sent via SendGrid to %s", to)
        except Exception as exc:
            logger.error("SendGrid send failed to %s: %s", to, exc)
            raise EmailDeliveryError(str(exc)) from exc

    def _send_via_mailgun(self, *, to: str, subject: str, html_body: str) -> None:
        try:
            import httpx

            api_key = getattr(settings, "MAILGUN_API_KEY", "")
            domain = getattr(settings, "MAILGUN_DOMAIN", "")
            if not api_key or not domain:
                logger.warning("MAILGUN_API_KEY or MAILGUN_DOMAIN not set.")
                return

            resp = httpx.post(
                f"https://api.mailgun.net/v3/{domain}/messages",
                auth=("api", api_key),
                data={
                    "from": self.from_addr,
                    "to": to,
                    "subject": subject,
                    "html": html_body,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            logger.info("Email sent via Mailgun to %s", to)
        except Exception as exc:
            logger.error("Mailgun send failed to %s: %s", to, exc)
            raise EmailDeliveryError(str(exc)) from exc


email_service = EmailService()
