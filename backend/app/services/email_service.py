import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

logger = logging.getLogger("finswarm.email")

async def send_reset_email(to_email: str, pin: str) -> bool:
    """
    Sends a 6-digit password reset PIN asynchronously.
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    
    # Strip all whitespace (including internal spaces from Gmail App Passwords)
    smtp_password = os.getenv("SMTP_PASSWORD", "").replace(" ", "").strip()
    
    if not smtp_user or not smtp_password:
        logger.warning("[EMAIL WARNING] SMTP credentials not set. Reset PIN printed to console only.")
        # Print clearly to the terminal for local development testing
        print(f"\n{'='*50}\n[LOCAL DEV] Password Reset PIN for {to_email}: {pin}\n{'='*50}\n")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = "FinSwarm Password Reset PIN"
        
        body = f"""Hello,

You have requested to reset your password on FinSwarm.
Your secure 6-digit password reset PIN is:

{pin}

This PIN is valid for 10 minutes. If you did not request this, please ignore this email.

Best regards,
FinSwarm Swarm Intelligence Team"""

        msg.attach(MIMEText(body, 'plain'))
        
        # Connect and send asynchronously (prevents FastAPI thread blocking)
        await aiosmtplib.send(
            msg,
            hostname=smtp_server,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=(smtp_port != 465),  # Use STARTTLS for 587
            use_tls=(smtp_port == 465)     # Use direct SSL/TLS for 465
        )
        
        logger.info(f"Successfully sent reset PIN email to {to_email}")
        return True
    except Exception as e:
        logger.exception(f"Failed to send reset email to {to_email}: {e}")
        return False