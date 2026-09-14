import os
import hmac
import hashlib
from typing import Optional
from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader
from .config import settings

API_KEY_NAME = "X-DriveScope-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def generate_share_signature(run_id: str, share_token: str) -> str:
    """Generate cryptographic signature for shareable read-only run links."""
    message = f"{run_id}:{share_token}:{settings.SECRET_KEY}"
    return hmac.new(settings.SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()[:16]


def verify_share_signature(run_id: str, share_token: str, signature: str) -> bool:
    """Verify validity of signed share link."""
    expected = generate_share_signature(run_id, share_token)
    return hmac.compare_digest(expected, signature)


def get_current_user(api_key: Optional[str] = Security(api_key_header)):
    """
    Lightweight auth dependency.
    If AUTH_ENABLED is False (default in development/minimal mode), allows open access.
    If AUTH_ENABLED is True, validates against configured API key.
    """
    auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    if not auth_enabled:
        return {"user": "developer", "role": "admin"}

    configured_key = os.getenv("DRIVESCOPE_API_KEY", "drivescope-secret-key-2026")
    if not api_key or api_key != configured_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return {"user": "authenticated_user", "role": "engineer"}
