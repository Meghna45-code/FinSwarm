import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("finswarm.email")

def send_reset_email(to_email: str, pin: str) -> bool:
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "").replace(" ", "")
    
    if not smtp_user or not smtp_password:
        logger.warning("[EMAIL WARNING] SMTP credentials not set. Reset PIN printed to console only.")
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
        
        # Connect and send
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Successfully sent reset PIN email to {to_email}")
        return True
    except Exception as e:
        logger.exception(f"Failed to send reset email to {to_email}: {e}")
        return False
