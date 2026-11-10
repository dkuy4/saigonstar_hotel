import base64
import hashlib
import logging
from typing import Optional
from cryptography.fernet import Fernet
from app.config import settings

logger = logging.getLogger(__name__)

def _get_fernet_instance() -> Fernet:
    """
    Derives a 32-byte URL-safe base64 key from configuration secret.
    Guarantees consistent encryption/decryption across application restarts.
    """
    secret = getattr(settings, "DOC_ENCRYPTION_KEY", None) or settings.JWT_SECRET
    key_bytes = hashlib.sha256(secret.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)

def encrypt_id_document(raw_id: str) -> str:
    """
    Encrypts identification document number before database storage (NFR-13).
    SECURITY REQUIREMENT: Never logs the plaintext ID.
    """
    if not raw_id:
        raise ValueError("ID document number cannot be empty")
    
    clean_id = str(raw_id).strip()
    fernet = _get_fernet_instance()
    encrypted_bytes = fernet.encrypt(clean_id.encode("utf-8"))
    return encrypted_bytes.decode("ascii")

def decrypt_id_document(cipher_text: str) -> str:
    """
    Decrypts identification document number (NFR-13).
    SECURITY REQUIREMENT: Never logs the plaintext ID.
    """
    if not cipher_text:
        return ""
    
    clean_cipher = str(cipher_text).strip()
    fernet = _get_fernet_instance()
    try:
        decrypted_bytes = fernet.decrypt(clean_cipher.encode("ascii"))
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to decrypt ID document ciphertext (length={len(clean_cipher)})")
        raise ValueError("Invalid encrypted document payload") from e

def mask_id_document(raw_id: str) -> str:
    """
    Masks document number for safe display (e.g. 079201009876 -> 0792****9876).
    """
    if not raw_id:
        return ""
    s = str(raw_id).strip()
    if len(s) <= 4:
        return "****"
    if len(s) <= 8:
        return s[:2] + "****" + s[-2:]
    return s[:4] + "****" + s[-4:]
