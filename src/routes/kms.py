"""Mock Cloud KMS Cryptographic Service using real AES-GCM encryption."""
import os
import base64
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.config import settings
from src.schemas.kms import (
    GenerateDataKeyRequest,
    GenerateDataKeyResponse,
    EncryptRequest,
    EncryptResponse,
    DecryptRequest,
    DecryptResponse,
)
from src.store.memory_store import memory_store

router = APIRouter(prefix="/kms", tags=["Cloud KMS Cryptography"])


def _get_aesgcm() -> AESGCM:
    """Instantiate AESGCM cipher using configured master key."""
    return AESGCM(settings.KMS_MASTER_KEY_BYTES)


@router.post(
    "/generate-data-key",
    response_model=GenerateDataKeyResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate 256-bit AES Data Encryption Key (DEK)",
)
async def generate_data_key(payload: Optional[GenerateDataKeyRequest] = None) -> GenerateDataKeyResponse:
    """Generates a cryptographically random 256-bit DEK, returning plaintext and encrypted ciphertext blob."""
    memory_store.increment_metric("crypto_operations_total")
    key_id = payload.key_id if (payload and payload.key_id) else "alias/schedulerbot-dek"

    # Generate 32 bytes (256 bits) of cryptographically secure random bytes
    dek_raw = os.urandom(32)
    plaintext_b64 = base64.b64encode(dek_raw).decode("utf-8")

    # Encrypt DEK with KMS master key using AES-256-GCM
    aesgcm = _get_aesgcm()
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext_b64.encode("utf-8"), None)
    ciphertext_blob = base64.b64encode(nonce + ciphertext).decode("utf-8")

    return GenerateDataKeyResponse(
        key_id=key_id,
        plaintext=plaintext_b64,
        ciphertext_blob=ciphertext_blob,
    )


@router.post(
    "/encrypt",
    response_model=EncryptResponse,
    status_code=status.HTTP_200_OK,
    summary="Encrypt Plaintext with KMS Master Key",
)
async def encrypt(payload: EncryptRequest) -> EncryptResponse:
    """Encrypts plaintext data using AES-256-GCM."""
    memory_store.increment_metric("crypto_operations_total")
    key_id = payload.key_id or "alias/schedulerbot-dek"

    plaintext_bytes = payload.plaintext.encode("utf-8")
    aesgcm = _get_aesgcm()
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)
    ciphertext_blob = base64.b64encode(nonce + ciphertext).decode("utf-8")

    return EncryptResponse(
        key_id=key_id,
        ciphertext_blob=ciphertext_blob,
    )


@router.post(
    "/decrypt",
    response_model=DecryptResponse,
    status_code=status.HTTP_200_OK,
    summary="Decrypt Ciphertext Blob with KMS Master Key",
)
async def decrypt(payload: DecryptRequest) -> DecryptResponse:
    """Decrypts ciphertext blob back to plaintext."""
    memory_store.increment_metric("crypto_operations_total")
    key_id = payload.key_id or "alias/schedulerbot-dek"

    try:
        raw_blob = base64.b64decode(payload.ciphertext_blob)
        if len(raw_blob) < 28:  # 12 bytes nonce + min 16 bytes tag
            raise ValueError("Ciphertext blob too short")
        nonce = raw_blob[:12]
        ciphertext = raw_blob[12:]
        aesgcm = _get_aesgcm()
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        plaintext = decrypted_bytes.decode("utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Decryption failed: {str(e)}",
        )

    return DecryptResponse(
        key_id=key_id,
        plaintext=plaintext,
    )
