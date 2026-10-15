"""Event schema and helpers for the handshake UI pipeline.

Never sends real keys — only fingerprints (first 8 hex chars of SHA-256).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any


def fingerprint(data: bytes) -> str:
    """Return first 8 hex characters of SHA-256 of *data*."""
    return hashlib.sha256(data).hexdigest()[:8]


def ciphertext_preview(data: bytes, max_hex: int = 48) -> str:
    """Return the first *max_hex* hex characters of *data*."""
    return data.hex()[:max_hex]


@dataclass
class StepEvent:
    """A single event in the handshake pipeline."""

    type: str  # "step", "plan", "aborted", "scorecard", "done"
    step: int = 0
    stage: str = ""
    id: str = ""
    title: str = ""
    actor: str = ""  # "alice", "bob", "system"
    status: str = "ok"  # "ok", "abort", "skip"
    data: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    bytes: int = 0

    def to_json(self) -> str:
        d = asdict(self)
        # Remove empty optional fields for cleanliness
        for k in ("stage", "id", "title", "actor"):
            if not d[k]:
                del d[k]
        if d["bytes"] == 0:
            del d["bytes"]
        if d["step"] == 0 and d["type"] != "step":
            del d["step"]
        return json.dumps(d, default=str)

    @staticmethod
    def plan_event(stages: list[dict[str, Any]]) -> "StepEvent":
        return StepEvent(type="plan", data={"stages": stages})

    @staticmethod
    def done_event(session_fingerprint: str, total_ms: float) -> "StepEvent":
        return StepEvent(
            type="done",
            data={
                "session_fingerprint": session_fingerprint,
                "total_ms": round(total_ms, 2),
            },
        )

    @staticmethod
    def aborted_event(reason: str, at_step: int) -> "StepEvent":
        return StepEvent(
            type="aborted",
            data={"reason": reason, "at_step": at_step},
        )


# Stage definitions
STAGES = [
    {
        "id": "quantum_key",
        "title": "1. Quantum key exchange (BB84)",
        "steps": ["bb84_prepare", "bb84_transmit", "bb84_measure", "bb84_sift"],
    },
    {
        "id": "eavesdropper_check",
        "title": "2. Eavesdropper check and key clean-up",
        "steps": ["bb84_qber", "bb84_error_correction", "bb84_privacy_amp"],
    },
    {
        "id": "pq_key",
        "title": "3. Post-quantum key (ML-KEM)",
        "steps": ["mlkem_keygen", "mlkem_encaps", "mlkem_decaps"],
    },
    {
        "id": "hybrid_mix",
        "title": "4. Hybrid mix (HKDF)",
        "steps": ["hkdf_combine"],
    },
    {
        "id": "confirm",
        "title": "5. Key confirmation",
        "steps": ["key_confirm"],
    },
    {
        "id": "secure_chat",
        "title": "6. Secure chat (AES-256-GCM)",
        "steps": ["secure_chat"],
    },
]

# Step number mapping
STEP_IDS = [
    "hello",           # 1
    "bb84_prepare",    # 2
    "bb84_transmit",   # 3
    "bb84_measure",    # 4
    "bb84_sift",       # 5
    "bb84_qber",       # 6
    "bb84_error_correction",  # 7
    "bb84_privacy_amp",       # 8
    "mlkem_keygen",    # 9
    "mlkem_encaps",    # 10
    "mlkem_decaps",    # 11
    "hkdf_combine",    # 12
    "key_confirm",     # 13
    "secure_chat",     # 14
]

# Which steps apply to each mode
MODE_STEPS: dict[str, set[str]] = {
    "hybrid": set(STEP_IDS),
    "pqc": {"hello", "mlkem_keygen", "mlkem_encaps", "mlkem_decaps",
            "hkdf_combine", "key_confirm", "secure_chat"},
    "qkd": {"hello", "bb84_prepare", "bb84_transmit", "bb84_measure",
            "bb84_sift", "bb84_qber", "bb84_error_correction",
            "bb84_privacy_amp", "hkdf_combine", "key_confirm", "secure_chat"},
    "classical": {"hello", "hkdf_combine", "key_confirm", "secure_chat"},
}


def step_number(step_id: str) -> int:
    """Return 1-based step number for a step id."""
    return STEP_IDS.index(step_id) + 1


def stage_for_step(step_id: str) -> str:
    """Return the stage id containing a given step."""
    for s in STAGES:
        if step_id in s["steps"]:
            return s["id"]
    return ""


def build_plan(mode: str) -> list[dict[str, Any]]:
    """Build the ordered plan of stages/steps for a given mode."""
    allowed = MODE_STEPS.get(mode, set())
    plan = []
    for stage in STAGES:
        steps = [s for s in stage["steps"] if s in allowed]
        if steps:
            plan.append({
                "id": stage["id"],
                "title": stage["title"],
                "steps": [
                    {"step": step_number(s), "id": s}
                    for s in steps
                ],
            })
    return plan
