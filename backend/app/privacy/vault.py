"""
Encrypted PII Vault using Fernet symmetric encryption.
Stores and resolves tokens (e.g. [PERSON_1]) to encrypted original values, scoped to patient.
"""
import base64
import os
from typing import Dict, Optional
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from backend.app.config import get_settings
from backend.app.models.db import PiiVaultEntry, generate_uuid, utc_now


def _get_fernet() -> Fernet:
    settings = get_settings()
    key = settings.VAULT_KEY
    if not key:
        # Default 32-byte urlsafe key for fallback dev
        key = base64.urlsafe_b64encode(b"medguard_dev_vault_key_32_bytes_").decode()
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        # If invalid key format, generate a safe dev key
        padded = base64.urlsafe_b64encode((key.ljust(32)[:32]).encode())
        return Fernet(padded)


def encrypt_value(value: str) -> str:
    f = _get_fernet()
    return f.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(encrypted_str: str) -> str:
    f = _get_fernet()
    return f.decrypt(encrypted_str.encode("utf-8")).decode("utf-8")


def store_vault_token(
    db: Session,
    patient_id: str,
    token: str,
    original_value: str
) -> PiiVaultEntry:
    """Store an encrypted token mapping in the vault for a given patient."""
    enc = encrypt_value(original_value)
    entry = PiiVaultEntry(
        id=generate_uuid(),
        patient_id=patient_id,
        token=token,
        encrypted_value=enc,
        created_at=utc_now(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_vault_map_for_patient(db: Session, patient_id: str) -> Dict[str, str]:
    """Retrieve decrypted token->value map for a patient."""
    entries = db.query(PiiVaultEntry).filter(PiiVaultEntry.patient_id == patient_id).all()
    mapping = {}
    for entry in entries:
        try:
            mapping[entry.token] = decrypt_value(entry.encrypted_value)
        except Exception:
            mapping[entry.token] = "[DECRYPTION_ERROR]"
    return mapping


def purge_vault_for_patient(db: Session, patient_id: str) -> int:
    """Purge all vault entries for patient on delete request."""
    count = db.query(PiiVaultEntry).filter(PiiVaultEntry.patient_id == patient_id).delete()
    db.commit()
    return count

