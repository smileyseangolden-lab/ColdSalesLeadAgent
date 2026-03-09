"""Email sending service with SMTP support."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import structlog
from app.core.security import decrypt_value
from app.core.config import settings

logger = structlog.get_logger()


def _add_tracking_pixel(body_html: str, tracking_id: str) -> str:
    """Insert a tracking pixel for open tracking."""
    pixel_url = f"{settings.API_URL}/api/v1/webhooks/email-tracking/open/{tracking_id}"
    pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none" />'
    if "</body>" in body_html:
        return body_html.replace("</body>", f"{pixel}</body>")
    return body_html + pixel


def _wrap_links(body_html: str, tracking_id: str) -> str:
    """Wrap links for click tracking."""
    import re
    def replace_link(match):
        url = match.group(1)
        if "email-tracking" in url:
            return match.group(0)
        tracked = f"{settings.API_URL}/api/v1/webhooks/email-tracking/click/{tracking_id}?url={url}"
        return f'href="{tracked}"'
    return re.sub(r'href="([^"]+)"', replace_link, body_html)


def _add_unsubscribe_footer(body: str, lead_email: str) -> str:
    """Add CAN-SPAM compliant unsubscribe footer."""
    footer = f"""

---
If you no longer wish to receive these emails, reply with "unsubscribe" or click here to opt out.
This email was sent by LeadFlow AI Platform.
"""
    return body + footer


def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password_encrypted: str,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
    signature_html: str = "",
    tracking_id: str | None = None,
    is_html: bool = False,
) -> bool:
    """Send an email via SMTP."""
    try:
        password = decrypt_value(smtp_password_encrypted)

        msg = MIMEMultipart("alternative")
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject

        # Add unsubscribe footer
        full_body = _add_unsubscribe_footer(body, to_email)
        if signature_html:
            full_body += f"\n\n{signature_html}"

        # Create HTML version
        html_body = full_body.replace("\n", "<br>")
        if tracking_id:
            html_body = _add_tracking_pixel(html_body, tracking_id)
            html_body = _wrap_links(html_body, tracking_id)

        msg.attach(MIMEText(full_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        # Add List-Unsubscribe header
        msg["List-Unsubscribe"] = f"<mailto:{from_email}?subject=unsubscribe>"

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, password)
            server.send_message(msg)

        logger.info("email_sent", to=to_email, subject=subject)
        return True

    except Exception as e:
        logger.error("email_send_error", to=to_email, error=str(e))
        return False


def substitute_variables(template: str, lead: dict) -> str:
    """Replace {{variable}} placeholders with lead data."""
    result = template
    replacements = {
        "{{first_name}}": lead.get("first_name", ""),
        "{{last_name}}": lead.get("last_name", ""),
        "{{full_name}}": lead.get("full_name", ""),
        "{{company_name}}": lead.get("company_name", ""),
        "{{job_title}}": lead.get("job_title", ""),
        "{{industry}}": lead.get("industry", "your industry"),
        "{{email}}": lead.get("email", ""),
    }
    for key, val in replacements.items():
        result = result.replace(key, val)

    # Handle custom fields: {{custom.key}}
    custom = lead.get("custom_fields", {})
    for key, val in custom.items():
        result = result.replace(f"{{{{custom.{key}}}}}", str(val))

    return result
