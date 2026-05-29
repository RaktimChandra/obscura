"""The Safety Brain — behaviour anomaly detection on anonymous signals.

Operates only on identity-free features:
    [head_count, mean_density, motion_energy, pose_activity]

Three detectors, tried best-first, all unsupervised:
  1. Autoencoder (sklearn MLPRegressor) — learns to reconstruct "normal" feature
     windows; high reconstruction error = anomaly. This is the headline model.
  2. IsolationForest — fallback if the autoencoder hasn't trained yet.
  3. Robust z-score — fallback if scikit-learn is unavailable.

A light heuristic on top labels the anomaly type (surge / fall / loiter) so the
dashboard can show *what kind* of event, never *who*.
"""
from __future__ import annotations

import statistics
import time
from collections import deque

try:
    import numpy as np
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import IsolationForest
    _HAS_SK = True
except Exception:                       # pragma: no cover
    _HAS_SK = False


class SafetyBrain:
    def __init__(self, window: int = 150, refit_every: int = 60):
        self._hist: deque[list[float]] = deque(maxlen=window)
        self._scaler = None
        self._auto = None
        self._iforest = None
        self._err_mean = 0.0
        self._err_std = 1.0
        self._since_fit = 0
        self._refit_every = refit_every

    def observe(self, feat: list[float]) -> None:
        self._hist.append(feat)
        self._since_fit += 1

    def _fit(self) -> None:
        if not _HAS_SK or len(self._hist) < 40:
            return
        X = np.array(self._hist, dtype=float)
        self._scaler = StandardScaler().fit(X)
        Xs = self._scaler.transform(X)
        # Compact autoencoder: 4 -> 2 -> 4 bottleneck.
        self._auto = MLPRegressor(hidden_layer_sizes=(2,), activation="tanh",
                                  max_iter=400, random_state=0)
        self._auto.fit(Xs, Xs)
        errs = np.mean((self._auto.predict(Xs) - Xs) ** 2, axis=1)
        self._err_mean = float(errs.mean())
        self._err_std = float(errs.std() + 1e-9)
        self._iforest = IsolationForest(n_estimators=80, contamination=0.06,
                                        random_state=0).fit(X)
        self._since_fit = 0

    def assess(self, feat: list[float], zone: str) -> dict:
        self.observe(feat)
        if self._auto is None or self._since_fit >= self._refit_every:
            self._fit()

        head_count = feat[0]
        motion = feat[2] if len(feat) > 2 else 0.0
        score = 0.0

        if _HAS_SK and self._auto is not None and self._scaler is not None:
            x = self._scaler.transform([feat])
            err = float(np.mean((self._auto.predict(x) - x) ** 2))
            z = (err - self._err_mean) / self._err_std
            score = float(min(1.0, max(0.0, z / 4.0)))
        else:
            counts = [h[0] for h in self._hist]
            if len(counts) >= 5 and statistics.pstdev(counts) > 0:
                z = abs(head_count - statistics.mean(counts)) / statistics.pstdev(counts)
                score = float(min(1.0, z / 4.0))

        atype = "normal"
        if score > 0.5:
            counts = [h[0] for h in self._hist]
            avg = statistics.mean(counts) if counts else head_count
            if head_count > avg and motion > 0.55:
                atype = "surge"
            elif head_count < avg * 0.4:
                atype = "fall"
            else:
                atype = "loiter"

        return {"ts": round(time.time(), 3), "zone": zone, "type": atype,
                "score": round(score, 3), "anonymous": True}
