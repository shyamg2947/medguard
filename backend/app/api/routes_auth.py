"""
Authentication Routes for MedGuard.
Supports password/token login, OTP simulation, and role provisioning.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.deps import get_current_user, get_db, hash_password, verify_password
from backend.app.models.db import User, generate_uuid, utc_now
from backend.app.models.schemas import LoginRequest, OtpRequest, TokenOut, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenOut)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates by display_token or phone_hash, or provisions demo user if matching demo token."""
    user = db.query(User).filter(
        (User.display_token == req.phone_or_token) | (User.phone_hash == req.phone_or_token)
    ).first()

    if not user:
        # Check if it is a standard demo role request (e.g. DEMO-SENIOR, DEMO-CLINICIAN, DEMO-CAREGIVER, DEMO-ADMIN)
        if req.phone_or_token.startswith("DEMO-"):
            role = req.phone_or_token.replace("DEMO-", "").lower()
            if role not in ["senior", "caregiver", "clinician", "admin"]:
                role = "senior"
            user = User(
                id=generate_uuid(),
                role=role,
                display_token=req.phone_or_token,
                preferred_language="en",
                active=True,
                created_at=utc_now(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

    return TokenOut(
        access_token=user.id,
        user=UserOut.model_validate(user),
    )


@router.post("/otp/request")
def request_otp(req: OtpRequest, db: Session = Depends(get_db)):
    """Generates an OTP (simulated 6-digit for demo)."""
    user = db.query(User).filter(User.phone_hash == req.phone).first()
    otp_code = "123456"  # Deterministic demo OTP
    if user:
        user.otp = otp_code
        db.commit()
    return {"message": "OTP sent", "otp_demo": otp_code}


@router.post("/otp/verify", response_model=TokenOut)
def verify_otp(phone: str, otp: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_hash == phone).first()
    if not user or (user.otp != otp and otp != "123456"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    return TokenOut(
        access_token=user.id,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.post("/logout")
def logout(user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out"}

