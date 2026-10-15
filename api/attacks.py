"""Attack demo endpoints: Eve, tamper, and replay."""

from __future__ import annotations

from typing import Any

from api.events import ciphertext_preview, fingerprint
from api.sessions import ChatSession
from bb84.session import run_bb84_local
from network.secure_channel import SecureChannelError


def run_eve_attack(
    qubits: int = 4000,
    eve_rate: float = 1.0,
    noise: float = 0.0,
    seed: int | None = None,
) -> dict[str, Any]:
    """Run BB84 with and without Eve, compare QBER.

    Returns:
        Dict with ``qber_with_eve``, ``qber_baseline``, ``theoretical``,
        ``decision``, ``abort_reason``.
    """
    # With Eve
    result_eve = run_bb84_local(
        n_qubits=qubits, eve_rate=eve_rate, noise=noise, seed=seed
    )
    # Without Eve (same seed for fairness)
    result_clean = run_bb84_local(
        n_qubits=qubits, eve_rate=0.0, noise=noise, seed=seed
    )
    theoretical = 0.25 * eve_rate
    decision = "abort" if not result_eve.accepted else "ok"
    abort_reason = result_eve.aborted_reason or ""

    return {
        "qber_with_eve": round(result_eve.qber, 6),
        "qber_baseline": round(result_clean.qber, 6),
        "theoretical": round(theoretical, 6),
        "eve_rate": eve_rate,
        "qubits": qubits,
        "decision": decision,
        "abort_reason": abort_reason,
    }


def run_tamper_attack(
    session: ChatSession,
    sender: str,
    text: str,
) -> dict[str, Any]:
    """Encrypt, flip one bit, try to deliver.

    Returns:
        Dict with ``rejected``, ``error``, ``ciphertext_hex_preview``.
    """
    if sender == "alice":
        encrypt_ch = session.alice_channel
        decrypt_ch = session.bob_channel
    else:
        encrypt_ch = session.bob_channel
        decrypt_ch = session.alice_channel

    ct_blob = encrypt_ch.encrypt(text.encode())
    ct_preview = ciphertext_preview(ct_blob)

    # Flip one bit in the ciphertext (after the nonce)
    tampered = bytearray(ct_blob)
    tampered[-1] ^= 0xFF
    try:
        decrypt_ch.decrypt(bytes(tampered))
        return {
            "rejected": False,
            "error": "",
            "ciphertext_hex_preview": ct_preview,
        }
    except SecureChannelError as e:
        # We need to also "consume" the real message so counters stay synced
        # Actually the tampered one failed so the counter didn't advance.
        # Deliver the real one to advance the counter
        decrypt_ch.decrypt(ct_blob)
        return {
            "rejected": True,
            "error": str(e),
            "ciphertext_hex_preview": ct_preview,
        }


def run_replay_attack(
    session: ChatSession,
    sender: str,
    text: str,
) -> dict[str, Any]:
    """Send normally, then replay the same ciphertext.

    Returns:
        Dict with ``first_delivery``, ``replay_rejected``, ``error``.
    """
    if sender == "alice":
        encrypt_ch = session.alice_channel
        decrypt_ch = session.bob_channel
    else:
        encrypt_ch = session.bob_channel
        decrypt_ch = session.alice_channel

    ct_blob = encrypt_ch.encrypt(text.encode())
    ct_preview = ciphertext_preview(ct_blob)

    # First delivery
    try:
        decrypt_ch.decrypt(ct_blob)
        first_ok = "ok"
    except SecureChannelError as e:
        first_ok = f"failed: {e}"

    # Replay the same ciphertext
    try:
        decrypt_ch.decrypt(ct_blob)
        return {
            "first_delivery": first_ok,
            "replay_rejected": False,
            "error": "",
            "ciphertext_hex_preview": ct_preview,
        }
    except SecureChannelError as e:
        return {
            "first_delivery": first_ok,
            "replay_rejected": True,
            "error": str(e),
            "ciphertext_hex_preview": ct_preview,
        }
