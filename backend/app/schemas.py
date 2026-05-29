"""Shared data shapes for OBSCURA — the contract between all modules.

If you change a field name here, every module and the frontend must agree.
Freeze these early; treat changes as a team decision.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------- Perception / anonymized features ----------
class Frame(BaseModel):
    """One unit of *anonymous* perception. Contains no identifying pixels —
    only counts, a coarse density grid, and pose keypoints."""
    frame_id: str
    ts: float
    zone_id: str
    head_count: int
    density_grid: List[List[float]]          # coarse occupancy heatmap
    pose_vectors: List[List[float]] = []      # per-person skeleton keypoints


# ---------- Differential privacy ----------
class StatResponse(BaseModel):
    value: float                              # noised aggregate
    epsilon_remaining: float                  # budget left for this zone
    suppressed: bool = False                  # True if group < k
    query: str = "count"
    zone: Optional[str] = None


# ---------- Safety brain ----------
class Alert(BaseModel):
    ts: float
    zone: str
    type: str                                 # surge | fall | loiter | normal
    score: float                              # anomaly score (higher = stranger)
    anonymous: bool = True                    # always true: never tied to an ID


# ---------- Break-glass de-anonymization ----------
class BreakglassRequest(BaseModel):
    record_id: str
    reason: str
    requester: str


class ShareSubmission(BaseModel):
    request_id: str
    holder_id: str
    share: str                                # "x:y" hex-encoded Shamir point


class BreakglassStatus(BaseModel):
    request_id: str
    record_id: str
    status: str                               # pending | unlocked | denied
    shares_collected: int
    shares_required: int
    revealed: Optional[str] = None            # plaintext, only once unlocked


# ---------- Audit log ----------
class AuditEntry(BaseModel):
    seq: int
    ts: float
    action: str
    approvers: List[str] = []
    record_id: Optional[str] = None
    reason: Optional[str] = None
    prev_hash: str
    entry_hash: str


class AuditHead(BaseModel):
    seq: int
    head_hash: str
    verified: bool


# ---------- Privacy auditor ----------
class PrivacyScore(BaseModel):
    attempts: int
    successful_reids: int
    score: float = Field(..., description="1 - (successful re-IDs / attempts)")
