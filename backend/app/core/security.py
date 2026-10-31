"""
WorkforceIQ Security and Authentication Services.
Handles password hashing via bcrypt, JWT access token generation, and token revocation.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set
import bcrypt
import jwt

from app.config import get_settings

settings = get_settings()

# In-memory revocation set for invalidated tokens (logout strategy)
_REVOKED_TOKENS: Set[str] = set()


def hash_password(password: str) -> str:
    """Hash plaintext password using bcrypt with salt."""
    salt = bcrypt.gensalt()
    pwd_bytes = password.encode("utf-8")
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    subject: str,
    role: str,
    email: str,
    employee_id: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate signed JWT access token with role claims."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": subject,
        "email": email,
        "role": role,
        "emp_id": employee_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": f"{employee_id}-{int(now.timestamp())}",
    }

    if extra_claims:
        payload.update(extra_claims)

    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT access token signature and expiration."""
    if is_token_revoked(token):
        return None
    try:
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return decoded
    except jwt.PyJWTError:
        return None


def revoke_token(token: str) -> None:
    """Invalidate token upon logout."""
    _REVOKED_TOKENS.add(token)


def is_token_revoked(token: str) -> bool:
    """Check whether token has been explicitly invalidated."""
    return token in _REVOKED_TOKENS
