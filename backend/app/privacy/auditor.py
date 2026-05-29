"""Privacy Auditor — adversarial re-identification.

This is a genuine red-team that runs against our own output. It enrolls the
ORB feature descriptors of original face crops into a gallery, then takes the
*redacted* version of each face and tries to match it back to the right person.

If anonymization works, the redacted crop has almost no recoverable structure,
so the matcher either finds nothing or guesses wrong. The fraction of failed
re-identifications becomes the published Privacy Guarantee Score. We are not
asserting privacy — we are measuring an attacker's inability to break it.
"""
from __future__ import annotations

import threading

try:
    import cv2
    import numpy as np
    _HAS_CV = True
except Exception:                       # pragma: no cover
    _HAS_CV = False


class PrivacyAuditor:
    def __init__(self, match_distance: int = 48, min_good_matches: int = 10):
        self.attempts = 0
        self.successful_reids = 0
        self._gallery: list[tuple[str, "np.ndarray"]] = []
        self._lock = threading.Lock()
        self._match_distance = match_distance
        self._min_good = min_good_matches
        if _HAS_CV:
            self._orb = cv2.ORB_create(nfeatures=150)
            self._matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def enroll(self, face_id: str, face_gray) -> None:
        """Register an original (pre-redaction) face the attacker 'knows'."""
        if not _HAS_CV:
            return
        _, des = self._orb.detectAndCompute(face_gray, None)
        if des is not None and len(des) >= 4:
            with self._lock:
                self._gallery.append((face_id, des))
                # keep the gallery bounded
                if len(self._gallery) > 200:
                    self._gallery.pop(0)

    def attempt_reid(self, redacted_gray, true_id: str) -> bool:
        """Try to match a redacted face back to a gallery identity."""
        with self._lock:
            self.attempts += 1
            gallery = list(self._gallery)
        if not _HAS_CV or not gallery:
            return False
        _, des = self._orb.detectAndCompute(redacted_gray, None)
        if des is None or len(des) < 4:
            return False
        best_id, best_score = None, 0
        for gid, gdes in gallery:
            try:
                matches = self._matcher.match(des, gdes)
            except Exception:
                continue
            good = sum(1 for m in matches if m.distance < self._match_distance)
            if good > best_score:
                best_score, best_id = good, gid
        success = best_id == true_id and best_score >= self._min_good
        if success:
            with self._lock:
                self.successful_reids += 1
        return success

    def score(self) -> dict:
        with self._lock:
            a, s = self.attempts, self.successful_reids
        score = 1.0 if a == 0 else round(1.0 - s / a, 4)
        return {"attempts": a, "successful_reids": s, "score": score}
