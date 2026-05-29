"""Tests for the differential-privacy engine."""
import statistics
from app.privacy.dp import DPEngine, PrivacyBudget, laplace_noise


def test_laplace_is_unbiased_with_expected_spread():
    s = [laplace_noise(1.0) for _ in range(20000)]
    assert abs(statistics.mean(s)) < 0.1            # mean ~ 0
    assert abs(statistics.pstdev(s) - 1.414) < 0.1  # stdev ~ sqrt(2)


def test_k_anonymity_suppresses_small_groups():
    eng = DPEngine()
    r = eng.private_count(3, group_size=3, zone="z")
    assert r["suppressed"] is True


def test_noised_count_is_close_but_not_exact():
    eng = DPEngine()
    diffs = []
    for _ in range(50):
        eng.budget.reset("z")
        r = eng.private_count(40, group_size=40, zone="z", epsilon=1.0)
        diffs.append(abs(r["value"] - 40))
    assert max(diffs) > 0           # noise actually applied
    assert statistics.mean(diffs) < 10  # but still useful


def test_budget_depletes_then_refuses():
    b = PrivacyBudget(total=2.0, regen_per_sec=0.0)
    assert b.try_spend("z", 1.0) is True
    assert b.try_spend("z", 1.0) is True
    assert b.try_spend("z", 1.0) is False   # exhausted, refuse


def test_budget_regenerates_over_time():
    import time
    b = PrivacyBudget(total=2.0, regen_per_sec=100.0)
    b.try_spend("z", 2.0)
    assert b.remaining("z") < 0.1
    time.sleep(0.05)
    assert b.remaining("z") > 1.0           # recovered
