"""Shamir's Secret Sharing over GF(p).

The secret S (an AES key, as an integer) is the constant term of a random
degree-(t-1) polynomial. Each holder gets one point (i, f(i) mod p). Any t
points reconstruct f and therefore f(0) = S via Lagrange interpolation. With
t-1 or fewer points, every value of S is equally likely — security is
information-theoretic, not merely computational.
"""
from __future__ import annotations

import secrets
from typing import List, Tuple

from ..config import SHAMIR_PRIME, SHAMIR_T, SHAMIR_N

Share = Tuple[int, int]


def _eval_poly(coeffs: List[int], x: int, prime: int) -> int:
    """Evaluate polynomial (Horner's method) at x mod prime."""
    acc = 0
    for c in reversed(coeffs):
        acc = (acc * x + c) % prime
    return acc


def split_secret(secret: int, t: int = SHAMIR_T, n: int = SHAMIR_N,
                 prime: int = SHAMIR_PRIME) -> List[Share]:
    """Split `secret` into n shares; any t reconstruct it."""
    if not (0 < t <= n):
        raise ValueError("require 0 < t <= n")
    if secret >= prime:
        raise ValueError("secret must be smaller than the prime field")
    # Constant term is the secret; the rest are uniformly random in GF(p).
    coeffs = [secret] + [secrets.randbelow(prime) for _ in range(t - 1)]
    return [(i, _eval_poly(coeffs, i, prime)) for i in range(1, n + 1)]


def _inverse(a: int, prime: int) -> int:
    """Modular inverse via Fermat's little theorem (prime modulus)."""
    return pow(a, prime - 2, prime)


def reconstruct(shares: List[Share], prime: int = SHAMIR_PRIME) -> int:
    """Recover the secret = f(0) from t (or more) shares via Lagrange."""
    if len(shares) < 2:
        raise ValueError("need at least t shares to reconstruct")
    secret = 0
    for j, (xj, yj) in enumerate(shares):
        num, den = 1, 1
        for m, (xm, _) in enumerate(shares):
            if m == j:
                continue
            num = (num * (-xm)) % prime
            den = (den * (xj - xm)) % prime
        lagrange_0 = (num * _inverse(den, prime)) % prime
        secret = (secret + yj * lagrange_0) % prime
    return secret % prime


# ---- helpers for encoding shares as transportable strings ----
def share_to_str(share: Share) -> str:
    x, y = share
    return f"{x}:{hex(y)[2:]}"


def share_from_str(s: str) -> Share:
    x_str, y_hex = s.split(":")
    return int(x_str), int(y_hex, 16)
