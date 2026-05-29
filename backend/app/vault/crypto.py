"""Authenticated encryption for sealed identity records.

Each identity (the original, un-redacted crop / metadata) is sealed under a
fresh 256-bit AES-GCM key. That key is never stored — it is immediately split
via Shamir and discarded, so the ciphertext is undecryptable until a quorum
of holders cooperates.
"""
from __future__ import annotations

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


def generate_key() -> bytes:
    """Fresh 256-bit key (32 bytes)."""
    return get_random_bytes(32)


def key_to_int(key: bytes) -> int:
    return int.from_bytes(key, "big")


def int_to_key(value: int) -> bytes:
    return value.to_bytes(32, "big")


def seal(plaintext: bytes, key: bytes) -> dict:
    """Encrypt plaintext under key. Returns nonce/ciphertext/tag (hex)."""
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return {
        "nonce": cipher.nonce.hex(),
        "ciphertext": ciphertext.hex(),
        "tag": tag.hex(),
    }


def unseal(sealed: dict, key: bytes) -> bytes:
    """Decrypt and verify. Raises ValueError on tampering or wrong key."""
    cipher = AES.new(key, AES.MODE_GCM, nonce=bytes.fromhex(sealed["nonce"]))
    return cipher.decrypt_and_verify(
        bytes.fromhex(sealed["ciphertext"]),
        bytes.fromhex(sealed["tag"]),
    )
