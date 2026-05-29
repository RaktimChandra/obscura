"""Differential privacy engine.

Releases aggregate statistics with calibrated Laplace noise so that the
presence or absence of any single individual is statistically undetectable,
while the aggregate stays useful.

Core guarantee (epsilon-DP): for a counting query with sensitivity 1,
adding noise drawn from Laplace(0, 1/epsilon) means two datasets differing in
one person produce output distributions within a factor e^epsilon of each
other. No observer can confidently tell whether you were in the frame.
"""
from __future__ import annotations

import math
import random
import threading
import time

from ..config import (
    EPSILON_DEFAULT,
    ZONE_EPSILON_BUDGET,
    COUNT_SENSITIVITY,
    K_ANON_THRESHOLD,
    EPSILON_REGEN_PER_SEC,
)


def laplace_noise(scale: float) -> float:
    """Sample Laplace(0, scale) via inverse-CDF transform.

    Draw u uniformly on [-0.5, 0.5); the inverse CDF of the Laplace
    distribution is  -scale * sign(u) * ln(1 - 2|u|).
    """
    u = random.random() - 0.5            # [-0.5, 0.5)
    abs_u = abs(u)
    # Guard the log against the (vanishingly rare) tail at |u| -> 0.5.
    inner = max(1.0 - 2.0 * abs_u, 1e-12)
    sign = 1.0 if u >= 0 else -1.0
    return -scale * sign * math.log(inner)


class PrivacyBudget:
    """Tracks epsilon spent per zone, with time-based regeneration.

    Each query spends epsilon; the spent amount leaks back toward zero at
    `regen_per_sec`. So the budget visibly drops under querying and recovers
    when querying eases. If a burst of queries exhausts it, further queries are
    refused until it regenerates — the "we refuse to over-query our citizens"
    guarantee, now demonstrable live.
    """

    def __init__(self, total: float = ZONE_EPSILON_BUDGET,
                 regen_per_sec: float = EPSILON_REGEN_PER_SEC):
        self._total = total
        self._regen = regen_per_sec
        self._spent: dict[str, float] = {}
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def _decayed_spend(self, zone: str) -> float:
        now = time.time()
        last = self._last.get(zone, now)
        spent = max(0.0, self._spent.get(zone, 0.0) - (now - last) * self._regen)
        self._spent[zone] = spent
        self._last[zone] = now
        return spent

    def remaining(self, zone: str) -> float:
        with self._lock:
            return round(self._total - self._decayed_spend(zone), 2)

    def try_spend(self, zone: str, epsilon: float) -> bool:
        with self._lock:
            spent = self._decayed_spend(zone)
            if spent + epsilon > self._total:
                return False
            self._spent[zone] = spent + epsilon
            return True

    def reset(self, zone: str | None = None) -> None:
        with self._lock:
            if zone is None:
                self._spent.clear(); self._last.clear()
            else:
                self._spent.pop(zone, None); self._last.pop(zone, None)


class DPEngine:
    """Differentially private query interface over aggregate counts."""

    def __init__(self, budget: PrivacyBudget | None = None):
        self.budget = budget or PrivacyBudget()

    def private_count(
        self,
        true_value: float,
        group_size: int,
        zone: str,
        epsilon: float = EPSILON_DEFAULT,
        sensitivity: float = COUNT_SENSITIVITY,
    ) -> dict:
        """Return a noised count, or a suppressed/refused result.

        Two protections stack:
          1. k-anonymity: groups smaller than the threshold are suppressed.
          2. epsilon-DP: Laplace noise scaled by sensitivity / epsilon.
        """
        # k-anonymity suppression
        if group_size < K_ANON_THRESHOLD:
            return {
                "value": 0.0,
                "epsilon_remaining": self.budget.remaining(zone),
                "suppressed": True,
                "zone": zone,
            }

        # Budget enforcement
        if not self.budget.try_spend(zone, epsilon):
            return {
                "value": 0.0,
                "epsilon_remaining": self.budget.remaining(zone),
                "suppressed": True,   # treated as suppressed: budget exhausted
                "zone": zone,
            }

        noisy = true_value + laplace_noise(sensitivity / epsilon)
        # Counts can't be negative; clamp and round for display honesty.
        noisy = max(0.0, noisy)
        return {
            "value": round(noisy, 2),
            "epsilon_remaining": self.budget.remaining(zone),
            "suppressed": False,
            "zone": zone,
        }
