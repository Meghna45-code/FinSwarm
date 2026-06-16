import secrets
import datetime
from datetime import timezone

def generate_secure_pin() -> tuple[str, datetime.datetime]:
    """
    Generates a cryptographically secure 6-digit PIN and a strict UTC expiration timestamp.
    """
    # secrets.randbelow is cryptographically secure (unlike the standard random module)
    pin = f"{secrets.randbelow(1000000):06d}"
    
    # Enforce the 10-minute rule using UTC to avoid server timezone bugs
    expires_at = datetime.datetime.now(timezone.utc) + datetime.timedelta(minutes=10)
    
    return pin, expires_at

def verify_reset_pin(user_provided_pin: str, db_stored_pin: str, db_expires_at: datetime.datetime) -> bool:
    """
    Validates that the PIN matches exactly AND has not expired.
    """
    # 1. Check if a PIN actually exists in the DB for this user
    if not db_stored_pin or not db_expires_at:
        return False
        
    # 2. Check if the PIN matches (string comparison)
    if user_provided_pin != db_stored_pin:
        return False
        
    # 3. Check if the 10 minutes have passed (Timezone-aware comparison)
    if datetime.datetime.now(timezone.utc) > db_expires_at:
        print("Auth Error: PIN is correct, but it has expired.")
        return False
        
    return True