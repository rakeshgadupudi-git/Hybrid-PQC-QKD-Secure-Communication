"""High-level BB84 session runner.

``run_bb84_local`` executes the entire BB84 protocol in-process
(Alice → Channel → Bob → sifting → QBER → error correction →
confirmation → privacy amplification) and is used by the dashboard,
benchmarks, and tests.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from bb84.eve import Eavesdropper
from bb84.postprocessing import (
    InsufficientKeyError,
    confirm_keys,
    estimate_qber,
    parity_error_correction,
    privacy_amplification,
    sift_keys,
)
from bb84.simulator import BB84Alice, BB84Bob, QuantumChannel
from config import Config


@dataclass
class BB84Result:
    """Outcome of a complete BB84 protocol run.

    Attributes:
        n_qubits: Number of qubits prepared.
        sifted_len: Length of the sifted key.
        sample_len: Number of bits used for QBER estimation.
        qber: Measured quantum bit error rate.
        accepted: Whether the session was accepted (QBER below threshold).
        aborted_reason: Reason for abort, or ``None``.
        leaked_bits: Parity bits leaked during error correction.
        final_key: The privacy-amplified key, or ``None`` if aborted.
        eve_intercepted: Number of qubits intercepted by Eve (0 if no Eve).
        timings: Timing breakdown in seconds.
    """

    n_qubits: int
    sifted_len: int
    sample_len: int
    qber: float
    accepted: bool
    aborted_reason: str | None = None
    leaked_bits: int = 0
    final_key: bytes | None = None
    eve_intercepted: int = 0
    timings: dict[str, float] = field(default_factory=dict)


def run_bb84_local(
    n_qubits: int = 4096,
    eve_rate: float = 0.0,
    noise: float = 0.0,
    seed: int | None = None,
    config: Config | None = None,
) -> BB84Result:
    """Run the BB84 protocol entirely in-process.

    Args:
        n_qubits: Number of qubits to prepare.
        eve_rate: Eve's intercept rate (0 = no Eve).
        noise: Channel bit-flip noise probability.
        seed: Optional seed for reproducible tests.
        config: Optional configuration (defaults to ``Config()``).

    Returns:
        A :class:`BB84Result` with all metrics.
    """
    cfg = config or Config()
    rng = np.random.default_rng(seed)
    timings: dict[str, float] = {}

    # 1. Alice prepares qubits
    t0 = time.perf_counter()
    alice = BB84Alice(rng=rng)
    batch = alice.prepare(n_qubits)
    timings["prepare"] = time.perf_counter() - t0

    # 2. Quantum channel (Eve + noise)
    t0 = time.perf_counter()
    eve = Eavesdropper(intercept_rate=eve_rate, rng=rng) if eve_rate > 0 else None
    channel = QuantumChannel(noise=noise, eavesdropper=eve, rng=rng)
    received = channel.transmit(batch)
    eve_intercepted = eve.intercepted_count if eve else 0
    timings["channel"] = time.perf_counter() - t0

    # 3. Bob measures
    t0 = time.perf_counter()
    bob = BB84Bob(rng=rng)
    bob_bits, bob_bases = bob.measure(received)
    timings["measure"] = time.perf_counter() - t0

    assert alice.bits is not None and alice.bases is not None

    # 4. Sifting
    t0 = time.perf_counter()
    alice_sifted, bob_sifted, _ = sift_keys(
        alice.bases, bob_bases, alice.bits, bob_bits
    )
    sifted_len = len(alice_sifted)
    timings["sifting"] = time.perf_counter() - t0

    if sifted_len < cfg.MIN_SIFTED_BITS:
        return BB84Result(
            n_qubits=n_qubits,
            sifted_len=sifted_len,
            sample_len=0,
            qber=0.0,
            accepted=False,
            aborted_reason=f"Insufficient sifted bits: {sifted_len} < {cfg.MIN_SIFTED_BITS}",
            eve_intercepted=eve_intercepted,
            timings=timings,
        )

    # 5. QBER estimation
    t0 = time.perf_counter()
    qber, alice_remaining, bob_remaining, sample_idx = estimate_qber(
        alice_sifted, bob_sifted, cfg.SAMPLE_FRACTION, rng
    )
    sample_len = len(sample_idx)
    timings["qber_estimation"] = time.perf_counter() - t0

    if qber > cfg.QBER_THRESHOLD:
        return BB84Result(
            n_qubits=n_qubits,
            sifted_len=sifted_len,
            sample_len=sample_len,
            qber=qber,
            accepted=False,
            aborted_reason=f"QBER {qber:.4f} exceeds threshold {cfg.QBER_THRESHOLD}",
            eve_intercepted=eve_intercepted,
            timings=timings,
        )

    # 6. Error correction
    t0 = time.perf_counter()
    corrected_bob, leaked_bits = parity_error_correction(
        alice_remaining, bob_remaining, qber, rng
    )
    timings["error_correction"] = time.perf_counter() - t0

    # 7. Key confirmation
    t0 = time.perf_counter()
    keys_match = confirm_keys(alice_remaining, corrected_bob)
    timings["confirmation"] = time.perf_counter() - t0

    if not keys_match:
        return BB84Result(
            n_qubits=n_qubits,
            sifted_len=sifted_len,
            sample_len=sample_len,
            qber=qber,
            accepted=False,
            aborted_reason="Key confirmation failed after error correction",
            leaked_bits=leaked_bits,
            eve_intercepted=eve_intercepted,
            timings=timings,
        )

    # 8. Privacy amplification
    t0 = time.perf_counter()
    pa_seed = os.urandom(32)
    try:
        final_key = privacy_amplification(
            alice_remaining, cfg.FINAL_KEY_BITS, leaked_bits, pa_seed
        )
    except InsufficientKeyError as exc:
        return BB84Result(
            n_qubits=n_qubits,
            sifted_len=sifted_len,
            sample_len=sample_len,
            qber=qber,
            accepted=False,
            aborted_reason=str(exc),
            leaked_bits=leaked_bits,
            eve_intercepted=eve_intercepted,
            timings=timings,
        )
    timings["privacy_amplification"] = time.perf_counter() - t0

    return BB84Result(
        n_qubits=n_qubits,
        sifted_len=sifted_len,
        sample_len=sample_len,
        qber=qber,
        accepted=True,
        leaked_bits=leaked_bits,
        final_key=final_key,
        eve_intercepted=eve_intercepted,
        timings=timings,
    )


def qber_sweep(
    rates: list[float] | NDArray[np.floating],
    n_qubits: int = 4096,
    trials: int = 5,
    noise: float = 0.0,
) -> pd.DataFrame:
    """Sweep QBER over a range of Eve intercept rates.

    Args:
        rates: List of intercept rates to test.
        n_qubits: Qubits per trial.
        trials: Number of trials per rate (results averaged).
        noise: Channel noise.

    Returns:
        DataFrame with columns ``rate``, ``qber_mean``, ``qber_std``.
    """
    rows: list[dict[str, float]] = []
    for rate in rates:
        qbers: list[float] = []
        for t in range(trials):
            result = run_bb84_local(
                n_qubits=n_qubits, eve_rate=float(rate), noise=noise, seed=t + 1000
            )
            qbers.append(result.qber)
        rows.append({
            "rate": float(rate),
            "qber_mean": float(np.mean(qbers)),
            "qber_std": float(np.std(qbers)),
        })
    return pd.DataFrame(rows)
