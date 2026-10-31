"""
FastAPI Dependencies: Database Session, Auth, Role Enforcement, and Auditing.
"""
import hashlib
import hmac
import os
from typing import Callable, Generator, List, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models.db import SessionLocal, User

security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}:{dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, expected_hash = hashed_password.split(":")
        dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(dk.hex(), expected_hash)
    except Exception:
        return False


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolves the current authenticated user from Bearer token (display_token or user id).
    In demo mode, allows demo user fallback if no token provided.
    """
    settings = get_settings()

    token_val = None
    if auth:
        token_val = auth.credentials

    if not token_val:
        # In demo mode, provide a default demo senior user if none supplied
        if settings.MODE == "demo":
            demo_user = db.query(User).filter(User.display_token == "DEMO-SENIOR").first()
            if demo_user:
                return demo_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
        )

    user = db.query(User).filter(
        (User.id == token_val) | (User.display_token == token_val)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        )
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


def require_role(allowed_roles: List[str]) -> Callable:
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: role '{user.role}' not permitted. Requires one of {allowed_roles}",
            )
        return user
    return role_checker

