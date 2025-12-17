from datetime import datetime, timedelta, timezone
import secrets
from jose import jwt

SECRET_KEY = "CHANGE_ME_SUPER_SECRET"
ALGORITHM = "HS256"
ACCESS_TTL_MINUTES = 5

def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),                        
        "jti": secrets.token_urlsafe(16),                    
        "exp": int((now + timedelta(minutes=ACCESS_TTL_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)
