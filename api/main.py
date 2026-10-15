"""FastAPI application: REST + WebSocket routes for the hybrid QKD-PQC UI.

CORS limited to the Vite dev server on localhost:5173.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.attacks import run_eve_attack, run_replay_attack, run_tamper_attack
from api.content import SCORECARD_CONTENT, STAGE_CONTENT, STEP_CONTENT
from api.events import STAGES, STEP_IDS, build_plan, fingerprint, ciphertext_preview
from api.runner import HandshakeRunner
from api.sessions import ChatSession, clear_sessions, create_session, get_session
from bb84.session import qber_sweep as _qber_sweep, run_bb84_local
from config import Config
from hybrid.combiner import HybridKeyCombiner
from network.secure_channel import SecureChannel, SecureChannelError
from pqc.mlkem import MLKEMKeyExchange

app = FastAPI(title="Hybrid QKD-PQC API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_pool = ThreadPoolExecutor(max_workers=4)
_project_root = Path(__file__).resolve().parent.parent


# ── Health ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ── Steps / content ──────────────────────────────────────────────────

@app.get("/api/steps")
async def get_steps():
    """Return stage, step, and scorecard content for the UI."""
    stages = []
    for s in STAGES:
        stage_c = STAGE_CONTENT.get(s["id"], {})
        steps = []
        for step_id in s["steps"]:
            sc = STEP_CONTENT.get(step_id, {})
            steps.append({
                "id": step_id,
                "title": sc.get("title", step_id),
                "simple": sc.get("simple", ""),
                "technical": sc.get("technical", ""),
            })
        stages.append({
            "id": s["id"],
            "title": s["title"],
            "simple": stage_c.get("simple", ""),
            "technical": stage_c.get("technical", ""),
            "steps": steps,
        })

    scorecard_items = []
    for sid in ("eve_detection", "pq_key", "hybrid", "aead", "replay", "confirm"):
        c = SCORECARD_CONTENT[sid]
        scorecard_items.append({
            "id": sid,
            "name": c["name"],
            "stops": c["stops"],
            "simple": c.get("simple", ""),
            "technical": c.get("technical", ""),
        })

    return {"stages": stages, "scorecard": scorecard_items}


# ── WebSocket run ────────────────────────────────────────────────────

@app.websocket("/ws/run")
async def ws_run(
    websocket: WebSocket,
    mode: str = Query("hybrid"),
    eve_rate: float = Query(0.0),
    noise: float = Query(0.0),
    qubits: int = Query(2048),
    message: str = Query("Hello Bob, this is Alice."),
):
    await websocket.accept()
    loop = asyncio.get_event_loop()
    runner = HandshakeRunner(
        mode=mode,
        eve_rate=eve_rate,
        noise=noise,
        n_qubits=qubits,
        message=message,
    )

    def collect_events():
        return list(runner.run())

    try:
        events = await loop.run_in_executor(_pool, collect_events)
        for ev in events:
            await websocket.send_text(ev.to_json())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "data": {"message": str(e)}}))
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ── Run pair (side-by-side) ──────────────────────────────────────────

class RunPairRequest(BaseModel):
    mode: str = "hybrid"
    qubits: int = 4000
    noise: float = 0.0
    message: str = "Hello Bob, this is Alice."
    attack_eve_rate: float = 1.0


@app.post("/api/run/pair")
async def run_pair(req: RunPairRequest):
    loop = asyncio.get_event_loop()
    seed = 42  # same seed for reproducibility

    def _run_normal():
        r = HandshakeRunner(
            mode=req.mode, eve_rate=0.0, noise=req.noise,
            n_qubits=req.qubits, message=req.message, seed=seed,
        )
        return [json.loads(e.to_json()) for e in r.run()]

    def _run_attack():
        r = HandshakeRunner(
            mode=req.mode, eve_rate=req.attack_eve_rate, noise=req.noise,
            n_qubits=req.qubits, message=req.message, seed=seed,
        )
        return [json.loads(e.to_json()) for e in r.run()]

    normal, attack = await asyncio.gather(
        loop.run_in_executor(_pool, _run_normal),
        loop.run_in_executor(_pool, _run_attack),
    )

    # Find where they diverge
    diverges_at_step = None
    for i, (n, a) in enumerate(zip(normal, attack)):
        if n.get("type") == "step" and a.get("type") == "step":
            if n.get("status") != a.get("status") or n.get("data") != a.get("data"):
                diverges_at_step = n.get("step", i)
                break
        elif n.get("type") != a.get("type"):
            diverges_at_step = n.get("step", a.get("step", i))
            break

    return {"normal": normal, "attack": attack, "diverges_at_step": diverges_at_step}


# ── BB84 lab ─────────────────────────────────────────────────────────

class Bb84LabRequest(BaseModel):
    qubits: int = 4000
    eve_rate: float = 0.0
    noise: float = 0.0
    seed: int | None = None


@app.post("/api/bb84/lab")
async def bb84_lab(req: Bb84LabRequest):
    loop = asyncio.get_event_loop()

    def _run():
        result = run_bb84_local(
            n_qubits=req.qubits,
            eve_rate=req.eve_rate,
            noise=req.noise,
            seed=req.seed,
        )
        return {
            "n_qubits": result.n_qubits,
            "sifted_len": result.sifted_len,
            "sample_len": result.sample_len,
            "qber": round(result.qber, 6),
            "accepted": result.accepted,
            "aborted_reason": result.aborted_reason,
            "leaked_bits": result.leaked_bits,
            "eve_intercepted": result.eve_intercepted,
            "timings": {k: round(v * 1000, 2) for k, v in result.timings.items()},
            "final_key_fingerprint": fingerprint(result.final_key) if result.final_key else None,
            "funnel": {
                "raw": result.n_qubits,
                "sifted": result.sifted_len,
                "after_sample": result.sifted_len - result.sample_len,
                "final_bits": 256 if result.accepted else 0,
            },
        }

    return await loop.run_in_executor(_pool, _run)


# ── QBER sweep ───────────────────────────────────────────────────────

@app.get("/api/bb84/sweep")
async def bb84_sweep(
    qubits: int = Query(4000),
    trials: int = Query(5),
    noise: float = Query(0.0),
):
    loop = asyncio.get_event_loop()

    def _run():
        rates = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        df = _qber_sweep(rates, n_qubits=qubits, trials=trials, noise=noise)
        return df.to_dict(orient="records")

    return await loop.run_in_executor(_pool, _run)


# ── Compare modes ────────────────────────────────────────────────────

@app.get("/api/compare")
async def compare_modes():
    loop = asyncio.get_event_loop()

    def _run():
        results = {}
        for mode in ("classical", "pqc", "qkd", "hybrid"):
            runner = HandshakeRunner(
                mode=mode, eve_rate=0.0, noise=0.0,
                n_qubits=2048, message="Compare test", seed=42,
            )
            events = list(runner.run())
            total_ms = 0.0
            total_bytes = 0
            step_count = 0
            for e in events:
                if e.type == "step":
                    step_count += 1
                    total_ms += e.duration_ms
                    total_bytes += e.bytes
                elif e.type == "done":
                    total_ms = e.data.get("total_ms", total_ms)
            results[mode] = {
                "total_ms": round(total_ms, 2),
                "bytes_exchanged": total_bytes,
                "step_count": step_count,
            }
        return results

    return await loop.run_in_executor(_pool, _run)


# ── Benchmarks ───────────────────────────────────────────────────────

@app.get("/api/benchmarks")
async def get_benchmarks():
    benchmarks_path = _project_root / "results" / "benchmarks.json"
    if not benchmarks_path.exists():
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content={
                "error": "benchmarks.json not found",
                "hint": "Run 'python -m benchmarks.run_benchmarks' first to generate benchmark data.",
            },
        )
    return json.loads(benchmarks_path.read_text(encoding="utf-8"))


# ── Chat ─────────────────────────────────────────────────────────────

class ChatStartRequest(BaseModel):
    mode: str = "hybrid"
    qubits: int = 2048
    noise: float = 0.0
    message: str = "Hello Bob, this is Alice."


@app.post("/api/chat/start")
async def chat_start(req: ChatStartRequest):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _pool, lambda: _create_chat_session(req.mode, req.qubits, req.noise)
    )


def _create_chat_session(mode: str, qubits: int, noise: float) -> dict[str, Any]:
    """Run a full handshake and create a chat session from it."""
    import os
    import hashlib
    from bb84.session import run_bb84_local
    from pqc.mlkem import MLKEMKeyExchange
    from hybrid.combiner import HybridKeyCombiner
    from classical.ecdh import X25519KeyExchange

    cfg = Config()
    qkd_key = None
    pq_secret = None
    classical_secret = None
    transcript_parts = []

    if mode in ("hybrid", "qkd"):
        result = run_bb84_local(n_qubits=qubits, eve_rate=0.0, noise=noise)
        if not result.accepted:
            return {"error": result.aborted_reason or "BB84 failed"}
        qkd_key = result.final_key
        transcript_parts.append(qkd_key)

    if mode in ("hybrid", "pqc"):
        kem = MLKEMKeyExchange(cfg.MLKEM_LEVEL)
        ek, dk = kem.generate_keypair()
        pq_secret, ct = kem.encapsulate(ek)
        _ = kem.decapsulate(dk, ct)
        transcript_parts.append(ct)

    if mode == "classical":
        kex_a = X25519KeyExchange()
        kex_b = X25519KeyExchange()
        pub_a = kex_a.generate()
        pub_b = kex_b.generate()
        classical_secret = kex_a.derive(pub_b)
        transcript_parts.append(pub_a + pub_b)

    transcript_hash = hashlib.sha256(b"".join(transcript_parts)).digest()
    combiner = HybridKeyCombiner(mode=mode, config=cfg)
    session_key = combiner.combine(
        qkd_key=qkd_key,
        pq_secret=pq_secret,
        classical_secret=classical_secret,
        transcript_hash=transcript_hash,
    )

    sfp = fingerprint(session_key)
    session = create_session(session_key, sfp, mode)
    return {"session_id": session.session_id, "session_fingerprint": sfp, "mode": mode}


class ChatSendRequest(BaseModel):
    session_id: str
    sender: str = "alice"
    text: str


@app.post("/api/chat/send")
async def chat_send(req: ChatSendRequest):
    session = get_session(req.session_id)
    if session is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Session not found"})

    if req.sender == "alice":
        encrypt_ch = session.alice_channel
        decrypt_ch = session.bob_channel
    else:
        encrypt_ch = session.bob_channel
        decrypt_ch = session.alice_channel

    ct_blob = encrypt_ch.encrypt(req.text.encode())
    pt = decrypt_ch.decrypt(ct_blob)

    return {
        "plaintext": req.text,
        "ciphertext_hex_preview": ciphertext_preview(ct_blob),
        "nonce_counter": encrypt_ch._send_counter - 1,
        "delivered_text": pt.decode(),
    }


# ── Attacks ──────────────────────────────────────────────────────────

class EveAttackRequest(BaseModel):
    qubits: int = 4000
    eve_rate: float = 1.0


@app.post("/api/attack/eve")
async def attack_eve(req: EveAttackRequest):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _pool, lambda: run_eve_attack(qubits=req.qubits, eve_rate=req.eve_rate)
    )


class TamperAttackRequest(BaseModel):
    session_id: str
    sender: str = "alice"
    text: str = "Secret message"


@app.post("/api/attack/tamper")
async def attack_tamper(req: TamperAttackRequest):
    session = get_session(req.session_id)
    if session is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return run_tamper_attack(session, req.sender, req.text)


class ReplayAttackRequest(BaseModel):
    session_id: str
    sender: str = "alice"
    text: str = "Secret message"


@app.post("/api/attack/replay")
async def attack_replay(req: ReplayAttackRequest):
    session = get_session(req.session_id)
    if session is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return run_replay_attack(session, req.sender, req.text)
