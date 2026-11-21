"""Unit tests for Mock Cloud KMS Cryptographic endpoints."""
import base64
import pytest
from fastapi.testclient import TestClient
from src.app import create_app
from src.store.memory_store import memory_store


@pytest.fixture(autouse=True)
def reset_store():
    """Reset store before each test."""
    memory_store.reset()
    yield
    memory_store.reset()


@pytest.fixture
def client():
    """Test client fixture."""
    app = create_app()
    return TestClient(app)


def test_generate_data_key_and_decrypt(client):
    """Test generating a DEK and decrypting its ciphertext blob to verify key integrity."""
    response = client.post("/kms/generate-data-key", json={"key_id": "alias/test-dek"})
    assert response.status_code == 200
    data = response.json()
    assert data["key_id"] == "alias/test-dek"
    assert "plaintext" in data
    assert "ciphertext_blob" in data

    # Verify plaintext is valid base64 of 32 bytes
    decoded_key = base64.b64decode(data["plaintext"])
    assert len(decoded_key) == 32

    # Decrypt the ciphertext blob using /kms/decrypt
    dec_response = client.post("/kms/decrypt", json={"ciphertext_blob": data["ciphertext_blob"]})
    assert dec_response.status_code == 200
    dec_data = dec_response.json()
    assert dec_data["plaintext"] == data["plaintext"]


def test_encrypt_decrypt_roundtrip(client):
    """Test encrypting plaintext string and decrypting back to identical text."""
    secret_text = "Highly Confidential Patient Health Information 12345"
    enc_response = client.post("/kms/encrypt", json={"plaintext": secret_text})
    assert enc_response.status_code == 200
    enc_data = enc_response.json()
    assert "ciphertext_blob" in enc_data

    # Decrypt
    dec_response = client.post("/kms/decrypt", json={"ciphertext_blob": enc_data["ciphertext_blob"]})
    assert dec_response.status_code == 200
    assert dec_response.json()["plaintext"] == secret_text


def test_decrypt_corrupted_ciphertext(client):
    """Test /kms/decrypt fails gracefully on malformed or corrupted ciphertext."""
    corrupted_blob = base64.b64encode(b"too_short").decode("utf-8")
    response = client.post("/kms/decrypt", json={"ciphertext_blob": corrupted_blob})
    assert response.status_code == 400
    assert "decryption failed" in response.json()["detail"].lower()


def test_encrypt_unicode_and_special_chars(client):
    """Test encrypting and decrypting unicode emoji and symbols."""
    text = "🔒 Special secret: 🚀 ¡Hola Mundo! 医疗记录"
    enc_res = client.post("/kms/encrypt", json={"plaintext": text})
    assert enc_res.status_code == 200
    dec_res = client.post("/kms/decrypt", json={"ciphertext_blob": enc_res.json()["ciphertext_blob"]})
    assert dec_res.status_code == 200
    assert dec_res.json()["plaintext"] == text


def test_generate_data_key_default_key_id(client):
    """Test generating DEK with default key_id."""
    res = client.post("/kms/generate-data-key", json={})
    assert res.status_code == 200
    assert res.json()["key_id"] == "alias/schedulerbot-dek"

