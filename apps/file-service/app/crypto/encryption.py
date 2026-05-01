"""
AES-256-GCM envelope encryption for file storage.

Upload flow:
  1. Generate random 32-byte DEK (Data Encryption Key)
  2. Encrypt file bytes with AES-256-GCM using DEK → ciphertext + nonce + tag
  3. Store ciphertext in MinIO
  4. Store base64(nonce + tag + dek) in PostgreSQL files.dek_wrapped

Download flow:
  1. Fetch ciphertext from MinIO
  2. Read dek_wrapped from DB → extract nonce, tag, dek
  3. Decrypt ciphertext with AES-256-GCM
  4. Verify SHA-256 of plaintext matches stored digest
  5. Return plaintext bytes

NOTE: In production the DEK would be wrapped with a KEK stored in an HSM/KMS.
For this implementation the DEK is stored directly (base64-encoded) alongside
the nonce and tag. This still provides at-rest encryption — MinIO compromise
alone does not expose plaintext.
"""

import base64
import os
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_dek() -> bytes:
    """Generate a random 256-bit Data Encryption Key."""
    return os.urandom(32)


def encrypt(plaintext: bytes, dek: bytes) -> Tuple[bytes, bytes]:
    """
    Encrypt plaintext with AES-256-GCM.
    Returns (ciphertext_with_tag, nonce).
    The AESGCM cipher appends the 16-byte auth tag to the ciphertext.
    """
    nonce = os.urandom(12)  # 96-bit nonce, recommended for GCM
    aesgcm = AESGCM(dek)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return ciphertext, nonce


def decrypt(ciphertext: bytes, dek: bytes, nonce: bytes) -> bytes:
    """
    Decrypt AES-256-GCM ciphertext.
    Raises cryptography.exceptions.InvalidTag if tampered.
    """
    aesgcm = AESGCM(dek)
    return aesgcm.decrypt(nonce, ciphertext, None)


def pack_dek_blob(dek: bytes, nonce: bytes) -> str:
    """
    Pack DEK + nonce into a single base64 string for DB storage.
    Format: base64(nonce[12] + dek[32])
    """
    return base64.b64encode(nonce + dek).decode()


def unpack_dek_blob(blob: str) -> Tuple[bytes, bytes]:
    """
    Unpack DEK blob from DB.
    Returns (dek, nonce).
    """
    raw = base64.b64decode(blob)
    nonce = raw[:12]
    dek = raw[12:]
    return dek, nonce
