"""Protection scorecard builder.

Produces six scorecard items from a finished (or aborted) run.
"""

from __future__ import annotations

from typing import Any

from api.content import SCORECARD_CONTENT


def build_scorecard(mode: str, sc: Any) -> list[dict[str, Any]]:
    """Build the six-item protection scorecard.

    Args:
        mode: Handshake mode.
        sc: A ``_ScorecardData`` instance from the runner.

    Returns:
        List of scorecard item dicts.
    """
    items: list[dict[str, Any]] = []

    # 1. Eve detection
    c = SCORECARD_CONTENT["eve_detection"]
    if mode in ("pqc", "classical"):
        status = "not_in_mode"
        evidence = "BB84 is not used in this mode."
    elif not sc.bb84_ran:
        status = "not_reached"
        evidence = "BB84 phase did not complete."
    elif sc.qber_ok:
        status = "active"
        evidence = f"QBER = {sc.qber:.4f}, below threshold {sc.qber_threshold}."
    else:
        status = "triggered"
        evidence = f"QBER = {sc.qber:.4f}, above threshold {sc.qber_threshold}. Eavesdropper detected!"
    items.append({
        "id": "eve_detection",
        "name": c["name"],
        "stops": c["stops"],
        "status": status,
        "evidence": evidence,
    })

    # 2. PQ key
    c = SCORECARD_CONTENT["pq_key"]
    if mode in ("qkd", "classical"):
        status = "not_in_mode"
        evidence = "ML-KEM is not used in this mode."
    elif not sc.pqc_ran:
        status = "not_reached"
        evidence = "PQC phase did not complete."
    elif sc.pqc_match:
        status = "active"
        evidence = f"ML-KEM decaps matches encaps (fingerprints: {sc.pqc_fingerprint_alice} = {sc.pqc_fingerprint_bob})."
    else:
        status = "failed"
        evidence = f"ML-KEM mismatch: {sc.pqc_fingerprint_alice} ≠ {sc.pqc_fingerprint_bob}."
    items.append({
        "id": "pq_key",
        "name": c["name"],
        "stops": c["stops"],
        "status": status,
        "evidence": evidence,
    })

    # 3. Hybrid
    c = SCORECARD_CONTENT["hybrid"]
    if mode not in ("hybrid",):
        status = "not_in_mode"
        evidence = "Hybrid combination is not used in this mode."
    elif not sc.hybrid_ran:
        status = "not_reached"
        evidence = "Hybrid key derivation did not complete."
    elif sc.session_match and sc.hybrid_had_both:
        status = "active"
        evidence = f"Both QKD and PQC keys mixed. Session fingerprints match ({sc.session_fingerprint_alice})."
    elif sc.session_match:
        status = "active"
        evidence = f"Session fingerprints match ({sc.session_fingerprint_alice})."
    else:
        status = "failed"
        evidence = f"Session fingerprint mismatch: {sc.session_fingerprint_alice} ≠ {sc.session_fingerprint_bob}."
    items.append({
        "id": "hybrid",
        "name": c["name"],
        "stops": c["stops"],
        "status": status,
        "evidence": evidence,
    })

    # 4. AEAD
    c = SCORECARD_CONTENT["aead"]
    if not sc.chat_ran:
        status = "not_reached"
        evidence = "Secure chat did not complete."
    elif sc.aead_roundtrip and sc.aead_tamper_rejected:
        status = "active"
        evidence = "Roundtrip OK. Tampered ciphertext was rejected."
    else:
        status = "failed"
        evidence = f"Roundtrip: {sc.aead_roundtrip}, tamper rejected: {sc.aead_tamper_rejected}."
    items.append({
        "id": "aead",
        "name": c["name"],
        "stops": c["stops"],
        "status": status,
        "evidence": evidence,
    })

    # 5. Replay
    c = SCORECARD_CONTENT["replay"]
    if not sc.chat_ran:
        status = "not_reached"
        evidence = "Secure chat did not complete."
    elif sc.aead_replay_rejected:
        status = "active"
        evidence = "Replayed message was rejected by counter check."
    else:
        status = "failed"
        evidence = "Replay was NOT rejected."
    items.append({
        "id": "replay",
        "name": c["name"],
        "stops": c["stops"],
        "status": status,
        "evidence": evidence,
    })

    # 6. Key confirmation
    c = SCORECARD_CONTENT["confirm"]
    if not sc.key_confirm_ran:
        status = "not_reached"
        evidence = "Key confirmation did not complete."
    elif sc.key_confirm_ok:
        status = "active"
        evidence = "HMAC tags match — both sides have the same key."
    else:
        status = "failed"
        evidence = "HMAC tags do not match."
    items.append({
        "id": "confirm",
        "name": c["name"],
        "stops": c["stops"],
        "status": status,
        "evidence": evidence,
    })

    return items
