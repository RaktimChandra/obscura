"""HTTP surface for OBSCURA."""
from __future__ import annotations

from collections import deque
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import schemas
from ..config import FEATURE_BUFFER_SIZE
from ..privacy.dp import DPEngine
from ..privacy.auditor import PrivacyAuditor
from ..privacy.assistant import InsightAssistant
from ..safety.brain import SafetyBrain
from ..vault import vault, audit

router = APIRouter()

feature_buffer: deque[dict] = deque(maxlen=FEATURE_BUFFER_SIZE)
dp_engine = DPEngine()
safety_brain = SafetyBrain()
auditor = PrivacyAuditor()
assistant = InsightAssistant(dp_engine, feature_buffer)


class AskRequest(BaseModel):
    question: str


@router.get("/stats", response_model=schemas.StatResponse)
def stats(zone: str = "zone-A", query: str = "count"):
    recent = [f for f in feature_buffer if f["zone_id"] == zone]
    if not recent:
        return schemas.StatResponse(value=0, epsilon_remaining=0,
                                    suppressed=True, query=query, zone=zone)
    true_count = recent[-1]["head_count"]
    res = dp_engine.private_count(true_count, group_size=true_count, zone=zone)
    return schemas.StatResponse(query=query, **res)


@router.get("/truth")
def truth(zone: str = "zone-A"):
    """The real (un-noised) count — for the demo's side-by-side honesty panel
    only. In production this endpoint would not exist."""
    recent = [f for f in feature_buffer if f["zone_id"] == zone]
    return {"zone": zone, "true_count": recent[-1]["head_count"] if recent else 0}


@router.get("/alerts", response_model=list[schemas.Alert])
def alerts():
    out, seen = [], set()
    for f in reversed(feature_buffer):
        if f["zone_id"] in seen:
            continue
        seen.add(f["zone_id"])
        feat = [f["head_count"], f["head_count"] / 16.0,
                f.get("_motion", 0.3), f.get("_pose_activity", 0.3)]
        out.append(schemas.Alert(**safety_brain.assess(feat, f["zone_id"])))
    return out


@router.post("/ask")
def ask(req: AskRequest):
    return assistant.answer(req.question)


@router.post("/breakglass/request", response_model=schemas.BreakglassStatus)
def breakglass_request(req: schemas.BreakglassRequest):
    try:
        return schemas.BreakglassStatus(**vault.open_request(
            req.record_id, req.reason, req.requester))
    except KeyError:
        raise HTTPException(404, "unknown record")


@router.post("/breakglass/share", response_model=schemas.BreakglassStatus)
def breakglass_share(sub: schemas.ShareSubmission):
    try:
        return schemas.BreakglassStatus(**vault.submit_share(
            sub.request_id, sub.holder_id, sub.share))
    except KeyError:
        raise HTTPException(404, "unknown request")


@router.get("/audit", response_model=list[schemas.AuditEntry])
def get_audit():
    return [schemas.AuditEntry(**e) for e in audit.entries()]


@router.get("/audit/head", response_model=schemas.AuditHead)
def get_audit_head():
    return schemas.AuditHead(**audit.head())


@router.get("/privacy-score", response_model=schemas.PrivacyScore)
def privacy_score():
    return schemas.PrivacyScore(**auditor.score())
