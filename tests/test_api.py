"""Tests for the FastAPI backend: events, runner, scorecard, routes, and no-secrets."""

from __future__ import annotations

import json
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient

from api.events import STAGES, STEP_IDS, build_plan, fingerprint
from api.main import app

client = TestClient(app)


# ── Helpers ──────────────────────────────────────────────────────────

def _ws_run(**params) -> list[dict[str, Any]]:
    """Run a WebSocket handshake and return all events."""
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"/ws/run?{qs}" if qs else "/ws/run"
    events = []
    with client.websocket_connect(url) as ws:
        while True:
            try:
                msg = ws.receive_text()
                events.append(json.loads(msg))
            except Exception:
                break
    return events


HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
B64_RE = re.compile(r"^[A-Za-z0-9+/=]{17,}$")


def _is_long_hex(s: str) -> bool:
    """Check if a string is a hex string longer than 16 chars."""
    return len(s) > 16 and HEX_RE.match(s) is not None


def _is_long_b64(s: str) -> bool:
    """Check if a string looks like base64 longer than 16 chars."""
    return len(s) > 16 and B64_RE.match(s) is not None


def _walk_values(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    """Walk all leaf values in a nested structure, returning (path, value)."""
    results = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            results.extend(_walk_values(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            results.extend(_walk_values(v, f"{path}[{i}]"))
    else:
        results.append((path, obj))
    return results


# ── Health ───────────────────────────────────────────────────────────

class TestHealth:
    def test_health(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ── Steps content ────────────────────────────────────────────────────

class TestSteps:
    def test_steps_coverage(self):
        r = client.get("/api/steps")
        assert r.status_code == 200
        data = r.json()

        # 6 stages
        assert len(data["stages"]) == 6

        # 14 steps total
        all_steps = []
        for stage in data["stages"]:
            assert stage["simple"], f"Stage {stage['id']} missing simple text"
            assert stage["technical"], f"Stage {stage['id']} missing technical text"
            for step in stage["steps"]:
                all_steps.append(step["id"])
                assert step["simple"], f"Step {step['id']} missing simple text"
                assert step["technical"], f"Step {step['id']} missing technical text"
        # Steps in the 6 stages (excludes hello which is step 1)
        assert len(all_steps) == 13  # 14 - 1 (hello is not in stages)

        # 6 scorecard items
        assert len(data["scorecard"]) == 6
        for item in data["scorecard"]:
            assert item["simple"], f"Scorecard {item['id']} missing simple text"
            assert item["technical"], f"Scorecard {item['id']} missing technical text"


# ── Hybrid run (no Eve) ─────────────────────────────────────────────

class TestHybridNoEve:
    def test_full_hybrid_run(self):
        events = _ws_run(mode="hybrid", eve_rate=0, noise=0, qubits=2048)
        types = [e["type"] for e in events]

        # Must have plan, steps, scorecard, done
        assert types[0] == "plan"
        assert "scorecard" in types
        assert types[-1] == "done"

        # All steps in order
        step_events = [e for e in events if e["type"] == "step"]
        step_ids = [e["id"] for e in step_events]
        assert "hello" in step_ids
        assert "secure_chat" in step_ids

        # hkdf_combine
        hkdf = next(e for e in step_events if e["id"] == "hkdf_combine")
        assert hkdf["data"]["match"] is True

        # key_confirm
        kc = next(e for e in step_events if e["id"] == "key_confirm")
        assert kc["data"]["ok"] is True

        # secure_chat self-test
        chat = next(e for e in step_events if e["id"] == "secure_chat")
        st = chat["data"]["self_test"]
        assert st["roundtrip"] is True
        assert st["tamper_rejected"] is True
        assert st["replay_rejected"] is True

        # Scorecard: all 6 active
        scorecard = next(e for e in events if e["type"] == "scorecard")
        items = scorecard["data"]["items"]
        assert len(items) == 6
        for item in items:
            assert item["status"] == "active", \
                f"Scorecard item {item['id']} is {item['status']}, expected active"


# ── Hybrid run with Eve ──────────────────────────────────────────────

class TestHybridWithEve:
    def test_eve_abort(self):
        events = _ws_run(mode="hybrid", eve_rate=1.0, noise=0, qubits=4000)
        types = [e["type"] for e in events]

        # Must have aborted
        assert "aborted" in types

        # QBER near 0.25
        qber_ev = next(e for e in events if e.get("id") == "bb84_qber")
        assert qber_ev["status"] == "abort"
        assert abs(qber_ev["data"]["qber"] - 0.25) < 0.05

        # Aborted at bb84_qber
        aborted = next(e for e in events if e["type"] == "aborted")
        assert aborted["data"]["at_step"] == 6

        # Scorecard: eve_detection is triggered, later items not_reached
        scorecard = next(e for e in events if e["type"] == "scorecard")
        items = {i["id"]: i for i in scorecard["data"]["items"]}
        assert items["eve_detection"]["status"] == "triggered"
        assert items["pq_key"]["status"] == "not_reached"
        assert items["aead"]["status"] == "not_reached"


# ── PQC, QKD, Classical modes ───────────────────────────────────────

class TestModes:
    def test_pqc_mode(self):
        events = _ws_run(mode="pqc", eve_rate=0, noise=0, qubits=2048)
        types = [e["type"] for e in events]
        assert "done" in types
        step_ids = {e["id"] for e in events if e["type"] == "step"}
        assert "bb84_prepare" not in step_ids
        assert "mlkem_keygen" in step_ids

        scorecard = next(e for e in events if e["type"] == "scorecard")
        items = {i["id"]: i for i in scorecard["data"]["items"]}
        assert items["eve_detection"]["status"] == "not_in_mode"
        assert items["pq_key"]["status"] == "active"

    def test_qkd_mode(self):
        events = _ws_run(mode="qkd", eve_rate=0, noise=0, qubits=2048)
        types = [e["type"] for e in events]
        assert "done" in types
        step_ids = {e["id"] for e in events if e["type"] == "step"}
        assert "bb84_prepare" in step_ids
        assert "mlkem_keygen" not in step_ids

        scorecard = next(e for e in events if e["type"] == "scorecard")
        items = {i["id"]: i for i in scorecard["data"]["items"]}
        assert items["pq_key"]["status"] == "not_in_mode"
        assert items["eve_detection"]["status"] == "active"

    def test_classical_mode(self):
        events = _ws_run(mode="classical", eve_rate=0, noise=0, qubits=2048)
        types = [e["type"] for e in events]
        assert "done" in types
        step_ids = {e["id"] for e in events if e["type"] == "step"}
        assert "bb84_prepare" not in step_ids
        assert "mlkem_keygen" not in step_ids

        scorecard = next(e for e in events if e["type"] == "scorecard")
        items = {i["id"]: i for i in scorecard["data"]["items"]}
        assert items["eve_detection"]["status"] == "not_in_mode"
        assert items["pq_key"]["status"] == "not_in_mode"
        assert items["hybrid"]["status"] == "not_in_mode"


# ── Run pair ─────────────────────────────────────────────────────────

class TestRunPair:
    def test_run_pair(self):
        r = client.post("/api/run/pair", json={
            "mode": "hybrid", "qubits": 4000, "noise": 0,
            "message": "Test", "attack_eve_rate": 1.0,
        })
        assert r.status_code == 200
        data = r.json()
        assert "normal" in data
        assert "attack" in data
        assert len(data["normal"]) > 0
        assert len(data["attack"]) > 0

        # Attack list should have aborted
        attack_types = [e["type"] for e in data["attack"]]
        assert "aborted" in attack_types

        # diverges_at_step should be set
        assert data["diverges_at_step"] is not None


# ── Attack routes ────────────────────────────────────────────────────

class TestAttacks:
    def test_eve_attack(self):
        r = client.post("/api/attack/eve", json={"qubits": 4000, "eve_rate": 1.0})
        assert r.status_code == 200
        data = r.json()
        assert abs(data["qber_with_eve"] - 0.25) < 0.05
        assert data["decision"] == "abort"

    def test_tamper_attack(self):
        # First create a session
        r = client.post("/api/chat/start", json={"mode": "hybrid", "qubits": 2048})
        assert r.status_code == 200
        sid = r.json()["session_id"]

        r = client.post("/api/attack/tamper", json={
            "session_id": sid, "sender": "alice", "text": "Secret",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["rejected"] is True

    def test_replay_attack(self):
        r = client.post("/api/chat/start", json={"mode": "hybrid", "qubits": 2048})
        assert r.status_code == 200
        sid = r.json()["session_id"]

        r = client.post("/api/attack/replay", json={
            "session_id": sid, "sender": "alice", "text": "Secret",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["first_delivery"] == "ok"
        assert data["replay_rejected"] is True


# ── No-secrets test ──────────────────────────────────────────────────

class TestNoSecrets:
    def test_no_long_hex_in_events(self):
        """Walk every JSON value and assert no hex/b64 string > 16 chars
        except ciphertext_hex_preview fields."""
        events = _ws_run(mode="hybrid", eve_rate=0, noise=0, qubits=2048)
        for ev in events:
            for path, val in _walk_values(ev):
                if not isinstance(val, str):
                    continue
                # Allow ciphertext_hex_preview
                if "ciphertext_hex_preview" in path:
                    continue
                # Check for long hex strings
                if _is_long_hex(val):
                    pytest.fail(
                        f"Long hex string found at {path}: '{val[:32]}...'"
                    )

    def test_fingerprints_are_8_hex(self):
        """All fields with 'fingerprint' in the name must be exactly 8 hex chars."""
        events = _ws_run(mode="hybrid", eve_rate=0, noise=0, qubits=2048)
        for ev in events:
            for path, val in _walk_values(ev):
                if "fingerprint" in path and isinstance(val, str) and val != "n/a":
                    assert len(val) == 8 and HEX_RE.match(val), \
                        f"Fingerprint at {path} is not 8 hex chars: '{val}'"
