"""Pydantic v2 schemas for Cloud KMS Cryptographic operations."""
from typing import Optional
from pydantic import BaseModel, ConfigDict


class GenerateDataKeyRequest(BaseModel):
    """Request to generate a Data Encryption Key (DEK)."""
    model_config = ConfigDict(extra="allow")

    key_id: Optional[str] = "alias/schedulerbot-dek"
    key_spec: Optional[str] = "AES_256"


class GenerateDataKeyResponse(BaseModel):
    """Response containing plaintext key and encrypted ciphertext blob."""
    model_config = ConfigDict(extra="allow")

    key_id: str
    plaintext: str  # Base64 encoded plaintext 32-byte key
    ciphertext_blob: str  # Base64 encoded encrypted DEK


class EncryptRequest(BaseModel):
    """Request to encrypt data using KMS master key."""
    model_config = ConfigDict(extra="allow")

    key_id: Optional[str] = "alias/schedulerbot-dek"
    plaintext: str  # Plain text or Base64 string


class EncryptResponse(BaseModel):
    """Encrypted ciphertext response."""
    model_config = ConfigDict(extra="allow")

    key_id: str
    ciphertext_blob: str  # Base64 encoded ciphertext


class DecryptRequest(BaseModel):
    """Request to decrypt ciphertext blob."""
    model_config = ConfigDict(extra="allow")

    key_id: Optional[str] = "alias/schedulerbot-dek"
    ciphertext_blob: str  # Base64 encoded ciphertext


class DecryptResponse(BaseModel):
    """Decrypted plaintext response."""
    model_config = ConfigDict(extra="allow")

    key_id: str
    plaintext: str  # Plain text result
