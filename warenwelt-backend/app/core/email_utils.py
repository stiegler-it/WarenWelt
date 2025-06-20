from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List, Optional, Dict, Any
from app.core.config import settings
import logging # For logging
from pathlib import Path # If using template folder

# Configure logging
logger = logging.getLogger(__name__)
# Example basic config for logger if not configured elsewhere at root
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Ensure MAIL_FROM is set, otherwise fastapi-mail can raise an error at initialization
if not settings.MAIL_FROM:
    logger.warning("MAIL_FROM not set in environment variables. Email sending will likely fail if attempted.")
    # You could set a default placeholder to allow app to start, but sending would fail.
    # Or, make the ConnectionConfig conditional / handle it in send_email.
    # For now, we rely on the check within send_email.

# ConnectionConfig should be created only if mail settings are somewhat complete.
# However, FastMail instance (fm) needs it at import time.
# A better approach might be to initialize FastMail instance lazily or within a function.
# For simplicity now, it's at module level.

_conf_dict = {
    "MAIL_USERNAME": settings.MAIL_USERNAME,
    "MAIL_PASSWORD": settings.MAIL_PASSWORD,
    "MAIL_FROM": settings.MAIL_FROM or "default@example.com", # Provide a fallback if None to avoid error with FastMail
    "MAIL_FROM_NAME": settings.MAIL_FROM_NAME,
    "MAIL_PORT": settings.MAIL_PORT,
    "MAIL_SERVER": settings.MAIL_SERVER,
    "MAIL_STARTTLS": settings.MAIL_STARTTLS,
    "MAIL_SSL_TLS": settings.MAIL_SSL_TLS,
    "USE_CREDENTIALS": settings.MAIL_USE_CREDENTIALS,
    "VALIDATE_CERTS": settings.MAIL_VALIDATE_CERTS,
}
# TEMPLATE_FOLDER setting for HTML templates (optional)
# if settings.TEMPLATE_FOLDER:
#    _conf_dict["TEMPLATE_FOLDER"] = Path(settings.TEMPLATE_FOLDER).resolve()


# Check if essential mail server settings are present before creating ConnectionConfig
# FastMail will raise error if MAIL_SERVER is None.
if settings.MAIL_SERVER and settings.MAIL_FROM:
    conf = ConnectionConfig(**_conf_dict)
    fm = FastMail(conf)
else:
    logger.warning("Core mail server settings (MAIL_SERVER, MAIL_FROM) are not configured. Email functionality will be disabled.")
    fm = None # FastMail instance will be None

class EmailSchema(BaseModel):
    email_to: List[EmailStr] # Changed from 'email' to 'email_to' for clarity
    subject: str
    # For body, can be str (plain text) or Dict (for templates)
    body_content: Union[str, Dict[str, Any]] # body -> body_content for clarity

from typing import Union # Needs to be at the top

async def send_email(
    recipients: List[EmailStr],
    subject: str,
    body: Union[str, Dict[str, Any]], # Can be plain text, HTML string, or dict for template
    template_name: Optional[str] = None, # If using fastapi-mail's template system
    subtype: MessageType = MessageType.plain # Default to plain, can be MessageType.html
    ) -> bool:

    if not fm: # If FastMail was not initialized due to missing core config
        logger.error("Mail system not initialized due to missing configuration. Cannot send email.")
        return False

    if not settings.MAIL_FROM: # Double check MAIL_FROM as it's critical
        logger.error("MAIL_FROM is not configured. Cannot send email.")
        return False

    message_data = {
        "subject": subject,
        "recipients": recipients,
    }
    if template_name:
        if not isinstance(body, dict):
            logger.error("Body must be a dictionary when using templates.")
            return False
        message_data["template_body"] = body # Pass the context dictionary
        # subtype is often implicitly html when using templates, but can be set.
        # fastapi-mail handles this.
    else: # Plain or HTML string content
        if not isinstance(body, str):
            logger.error("Body must be a string if not using templates.")
            return False
        message_data["body"] = body
        message_data["subtype"] = subtype


    message = MessageSchema(**message_data)

    try:
        await fm.send_message(message, template_name=template_name)
        logger.info(f"Email sent successfully to {recipients}. Subject: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipients}. Subject: {subject}. Error: {e}", exc_info=True)
        return False

# Example usage (conceptual, will be integrated into payout_service):
# async def send_payout_notification_example(supplier_email: EmailStr, payout_amount: Decimal, payout_number: str):
#     subject = f"Ihre Auszahlung {payout_number} bei WarenWelt"
#     plain_text_body = (
#         f"Guten Tag,\n\n"
#         f"eine Auszahlung über {payout_amount:.2f} EUR mit der Nummer {payout_number} wurde für Sie veranlasst.\n\n"
#         f"Mit freundlichen Grüßen,\n"
#         f"Ihr WarenWelt Team"
#     )
#     # HTML body example (if using HTML emails)
#     # html_body = f"""
#     # <p>Guten Tag,</p>
#     # <p>eine Auszahlung über <strong>{payout_amount:.2f} EUR</strong> mit der Nummer <strong>{payout_number}</strong> wurde für Sie veranlasst.</p>
#     # <p>Mit freundlichen Grüßen,<br>Ihr WarenWelt Team</p>
#     # """
#     # success = await send_email(
#     #     recipients=[supplier_email],
#     #     subject=subject,
#     #     body=plain_text_body, # or html_body for HTML
#     #     subtype=MessageType.plain # or MessageType.html
#     # )
#     # if success:
#     #     print("Payout notification email sent.")
#     # else:
#     #     print("Failed to send payout notification email.")
