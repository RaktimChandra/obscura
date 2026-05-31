"""Edge anonymization engine.

Production path (RealAnonymizer): detects faces with OpenCV's res10 DNN, blurs
them, derives anonymous features (head_count, density, motion, pose activity),
and feeds the Privacy Auditor (enroll original crop, then attempt re-ID on the
blurred crop). Pose uses MediaPipe when installed.

Dev/demo path (SyntheticFeed): emits the same Frame shape with periodic crowd
surges, and synthesizes textured "faces" so the auditor's red-team runs with no
camera and no heavy dependencies.
"""
from __future__ import annotations

import math
import random
import time
import uuid

try:
    import cv2
    import numpy as np
    _HAS_CV = True
except Exception:                       # pragma: no cover
    _HAS_CV = False

GRID = 4


def _empty_grid() -> list[list[float]]:
    return [[0.0] * GRID for _ in range(GRID)]


def _synthetic_face(seed: int):
    """Build a 64x64 grayscale 'face' with enough structure for ORB to grab."""
    if not _HAS_CV:
        return None
    rng = random.Random(seed)
    img = np.full((64, 64), 128, np.uint8)
    for _ in range(6):
        c = (rng.randint(0, 63), rng.randint(0, 63))
        cv2.circle(img, c, rng.randint(4, 14), rng.randint(0, 255), -1)
    for _ in range(4):
        cv2.line(img, (rng.randint(0, 63), rng.randint(0, 63)),
                 (rng.randint(0, 63), rng.randint(0, 63)), rng.randint(0, 255), 2)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    return img


def redact(face_gray):
    """Blur a face crop beyond recovery."""
    return cv2.GaussianBlur(face_gray, (45, 45), 30) if _HAS_CV else face_gray


class SyntheticFeed:
    def __init__(self, zone_id: str = "zone-A"):
        self.zone_id = zone_id
        self.t = 0
        self.base = 18

    def next_frame(self):
        """Return (feature_dict, faces) where faces is a list of
        (face_id, original_gray, redacted_gray) for the auditor."""
        self.t += 1
        baseline = self.base + 6 * math.sin(self.t / 25.0)
        surge = random.randint(25, 45) if self.t % 40 == 0 else 0
        head_count = max(0, int(baseline + random.gauss(0, 2) + surge))

        grid = _empty_grid()
        for _ in range(head_count):
            grid[random.randrange(GRID)][random.randrange(GRID)] += 1.0
        motion = min(1.0, 0.3 + surge / 45.0 + random.random() * 0.2)

        faces = []
        if _HAS_CV:
            for k in range(min(head_count, 4)):     # sample a few faces to audit
                fid = f"person-{(self.t + k) % 12}"
                orig = _synthetic_face(hash(fid) & 0xFFFF)
                faces.append((fid, orig, redact(orig)))

        feat = {
            "frame_id": uuid.uuid4().hex[:12],
            "ts": round(time.time(), 3),
            "zone_id": self.zone_id,
            "head_count": head_count,
            "density_grid": grid,
            "pose_vectors": [],
            "_motion": round(motion, 3),
            "_pose_activity": round(motion * random.uniform(0.6, 1.0), 3),
        }
        return feat, faces


class RealAnonymizer:
    """OpenCV + MediaPipe path. Run on your machine with a video or webcam."""

    def __init__(self, zone_id: str = "zone-A",
                 proto="models/deploy.prototxt",
                 weights="models/res10_300x300_ssd_iter_140000.caffemodel"):
        import cv2
        self.cv2 = cv2
        self.zone_id = zone_id
        self.prev_gray = None
        self.net = cv2.dnn.readNetFromCaffe(proto, weights)
        import os as _os
        # Confidence threshold for the DNN. Lower catches more (smaller/angled)
        # faces. Tunable via OBSCURA_FACE_CONF (default 0.35 for crowd footage).
        self.conf = float(_os.environ.get("OBSCURA_FACE_CONF", "0.35"))
        # Haar cascade fallback catches faces the DNN misses (e.g. small ones).
        try:
            self._haar = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        except Exception:
            self._haar = None
        self._pose = None
        try:
            import mediapipe as mp
            self._pose = mp.solutions.pose.Pose(model_complexity=0)
            self._mp = mp
        except Exception:
            self._pose = None

    def process(self, frame, auditor=None):
        """Return (redacted_frame, feature_dict). Faces are redacted before any
        feature leaves this method. If an auditor is given, it enrolls the
        original crop then attempts re-ID on the blurred crop."""
        cv2 = self.cv2
        h, w = frame.shape[:2]
        boxes = []
        # --- primary: res10 DNN detector ---
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
                                     (300, 300), (104, 177, 123))
        self.net.setInput(blob)
        det = self.net.forward()
        for i in range(det.shape[2]):
            if det[0, 0, i, 2] < self.conf:
                continue
            x1, y1, x2, y2 = (det[0, 0, i, 3:7] * [w, h, w, h]).astype(int)
            boxes.append((max(0, x1), max(0, y1), min(w, x2), min(h, y2)))
        # --- fallback: Haar cascade for smaller / angled faces ---
        if self._haar is not None:
            gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            for (hx, hy, hw_, hh_) in self._haar.detectMultiScale(
                    gray_full, scaleFactor=1.1, minNeighbors=4, minSize=(24, 24)):
                boxes.append((hx, hy, hx + hw_, hy + hh_))
        # --- redact every detected face (strong pixelate + blur) ---
        count = 0
        for idx, (x1, y1, x2, y2) in enumerate(boxes):
            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                continue
            count += 1
            orig_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            # pixelate: shrink then upscale (mosaic) + heavy blur = irreversible
            rh, rw = roi.shape[:2]
            small = cv2.resize(roi, (max(1, rw // 12), max(1, rh // 12)),
                               interpolation=cv2.INTER_LINEAR)
            roi_red = cv2.resize(small, (rw, rh), interpolation=cv2.INTER_NEAREST)
            roi_red = cv2.GaussianBlur(roi_red, (31, 31), 20)
            frame[y1:y2, x1:x2] = roi_red
            if auditor is not None:
                fid = f"{self.zone_id}-{idx}"
                auditor.enroll(fid, orig_gray)
                red_gray = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
                auditor.attempt_reid(red_gray, fid)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        motion = 0.0
        if self.prev_gray is not None:
            motion = float(min(1.0, cv2.absdiff(gray, self.prev_gray).mean() / 25.0))
        self.prev_gray = gray

        pose_activity, pose_vectors = 0.0, []
        if self._pose is not None:
            res = self._pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if res.pose_landmarks:
                pts = [[lm.x, lm.y] for lm in res.pose_landmarks.landmark]
                pose_vectors = pts
                pose_activity = motion

        feat = {
            "frame_id": uuid.uuid4().hex[:12], "ts": round(time.time(), 3),
            "zone_id": self.zone_id, "head_count": count,
            "density_grid": _empty_grid(), "pose_vectors": pose_vectors,
            "_motion": round(motion, 3), "_pose_activity": round(pose_activity, 3),
        }
        return frame, feat


def mjpeg_stream(video_source, anonymizer: "RealAnonymizer", redacted=True,
                 auditor=None):
    """Yield multipart MJPEG frames from a video file path or webcam index.
    Set redacted=False to stream the raw feed for the side-by-side reveal."""
    import cv2
    cap = cv2.VideoCapture(video_source)
    while True:
        ok, frame = cap.read()
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)   # loop the clip
            continue
        out, _ = anonymizer.process(frame.copy(), auditor=auditor) if redacted \
            else (frame, None)
        ok, buf = cv2.imencode(".jpg", out)
        if not ok:
            continue
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
