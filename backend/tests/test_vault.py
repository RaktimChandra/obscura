"""Tests for Shamir secret sharing, AES sealing, and the audit chain."""
import os
from app.vault import shamir, crypto


def test_shamir_any_t_of_n_reconstructs():
    secret = int.from_bytes(os.urandom(31), "big")
    shares = shamir.split_secret(secret, t=2, n=3)
    assert shamir.reconstruct(shares[:2]) == secret
    assert shamir.reconstruct([shares[0], shares[2]]) == secret
    assert shamir.reconstruct([shares[1], shares[2]]) == secret


def test_shamir_share_serialization_roundtrip():
    s = (2, 123456789)
    assert shamir.share_from_str(shamir.share_to_str(s)) == s


def test_aes_seal_unseal_roundtrip():
    key = crypto.generate_key()
    sealed = crypto.seal(b"identity data", key)
    assert crypto.unseal(sealed, key) == b"identity data"


def test_aes_wrong_key_fails():
    sealed = crypto.seal(b"x", crypto.generate_key())
    import pytest
    with pytest.raises(ValueError):
        crypto.unseal(sealed, crypto.generate_key())
