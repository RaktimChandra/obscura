"""Private insight assistant.

A natural-language front door to the analytics — but one that is structurally
incapable of leaking an individual, because the ONLY data it can reach is the
differentially-private aggregate layer. It parses intent, calls the DP engine,
and phrases the noised answer. There is no code path from here to a raw record.

Deliberately rule-based (no external LLM) so it is deterministic, offline, and
fully auditable — you can prove exactly what it can and cannot return. An LLM
could phrase the replies more fluently, but it would still only ever see the
same DP outputs; the guarantee is in the wiring, not the model.
"""
from __future__ import annotations

import re


class InsightAssistant:
    def __init__(self, dp_engine, feature_buffer):
        self.dp = dp_engine
        self.buffer = feature_buffer

    def _zone(self, q: str) -> str:
        m = re.search(r"zone[-\s]?([a-z0-9]+)", q)
        return f"zone-{m.group(1).upper()}" if m else "zone-A"

    def _recent(self, zone: str):
        return [f for f in self.buffer if f["zone_id"] == zone]

    def answer(self, question: str) -> dict:
        q = question.lower().strip()
        zone = self._zone(q)
        recent = self._recent(zone)

        if not recent:
            return {"answer": f"I have no recent readings for {zone}.",
                    "private": True, "value": None, "zone": zone}

        # Intent: count / occupancy
        if any(k in q for k in ("how many", "count", "people", "crowd", "occupanc")):
            true_count = recent[-1]["head_count"]
            res = self.dp.private_count(true_count, group_size=true_count, zone=zone)
            if res["suppressed"]:
                return {"answer": (f"There are too few people in {zone} to report a "
                                   "number without risking someone's privacy."),
                        "private": True, "value": None, "zone": zone}
            return {"answer": (f"Approximately {round(res['value'])} people in {zone} "
                               "right now (privacy-protected estimate)."),
                    "private": True, "value": res["value"], "zone": zone}

        # Intent: busy / unusual / safe
        if any(k in q for k in ("busy", "surge", "unusual", "safe", "crowded", "anomal")):
            counts = [f["head_count"] for f in recent[-30:]]
            avg = sum(counts) / len(counts)
            latest = counts[-1]
            if latest > avg * 1.6:
                verdict = "busier than usual — a possible crowd surge"
            elif latest < avg * 0.5:
                verdict = "quieter than usual"
            else:
                verdict = "within its normal range"
            return {"answer": f"{zone} is currently {verdict}.",
                    "private": True, "value": None, "zone": zone}

        return {"answer": ("I can only answer questions about privacy-protected "
                           "aggregates — try 'how many people in zone A?' or "
                           "'is zone A unusually busy?'"),
                "private": True, "value": None, "zone": zone}
