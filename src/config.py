"""Configuration module for Mock API Server."""
import os
import hashlib
from typing import Optional


class Settings:
    """Application settings with environment variable override support."""

    APP_NAME: str = os.getenv("APP_NAME", "MockAPI_Server")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Meta Webhook Handshake & Signature
    WEBHOOK_VERIFY_TOKEN: str = os.getenv("WEBHOOK_VERIFY_TOKEN", "mock_verify_token_12345")
    APP_SECRET: str = os.getenv("APP_SECRET", "mock_meta_app_secret_abc123")

    # Meta Graph Defaults
    DEFAULT_PHONE_NUMBER_ID: str = os.getenv("DEFAULT_PHONE_NUMBER_ID", "109876543210987")
    WABA_ID: str = os.getenv("WABA_ID", "wh_biz_acc_123456")

    # Cloud KMS Mock Master Key (must be 32 bytes for AES-256)
    _raw_kms_key: str = os.getenv(
        "KMS_MASTER_KEY",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    )

    @property
    def KMS_MASTER_KEY_BYTES(self) -> bytes:
        """Returns a 32-byte master encryption key derived deterministically from config."""
        try:
            raw_bytes = bytes.fromhex(self._raw_kms_key)
            if len(raw_bytes) == 32:
                return raw_bytes
        except ValueError:
            pass
        return hashlib.sha256(self._raw_kms_key.encode("utf-8")).digest()


settings = Settings()
