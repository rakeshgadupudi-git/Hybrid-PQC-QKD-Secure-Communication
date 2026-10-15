"""BB84 classical post-processing: sifting, QBER, error correction,
key confirmation and privacy amplification.
"""

from __future__ import annotations

import hashlib
import secrets

import numpy as np
from numpy.typing import NDArray


class InsufficientKeyError(Exception):
    """Raised when the remaining key material is too short for privacy amplification."""


# ── Sifting ────────────────────────────────────────────────────────────


def sift_keys(
    alice_bases: NDArray[np.uint8],
    bob_bases: NDArray[np.uint8],
    alice_bits: NDArray[np.uint8],
    bob_bits: NDArray[np.uint8],
) -> tuple[NDArray[np.uint8], NDArray[np.uint8], NDArray[np.intp]]:
    """Keep only the positions where Alice and Bob chose the same basis.

    Args:
        alice_bases: Alice's preparation bases.
        bob_bases:   Bob's measurement bases.
        alice_bits:  Alice's raw bit string.
        bob_bits:    Bob's measured bit string.

    Returns:
        Tuple ``(alice_sifted, bob_sifted, kept_indices)``.
    """
    match = alice_bases == bob_bases
    kept = np.nonzero(match)[0]
    return alice_bits[kept], bob_bits[kept], kept


# ── QBER estimation ───────────────────────────────────────────────────


def estimate_qber(
    alice_sifted: NDArray[np.uint8],
    bob_sifted: NDArray[np.uint8],
    sample_fraction: float,
    rng: np.random.Generator,
) -> tuple[float, NDArray[np.uint8], NDArray[np.uint8], NDArray[np.intp]]:
    """Estimate the quantum bit error rate by revealing a random sample.

    The sampled bits are **discarded** from the key.

    Args:
        alice_sifted: Alice's sifted bits.
        bob_sifted:   Bob's sifted bits.
        sample_fraction: Fraction of sifted bits to sacrifice (0, 1).
        rng: NumPy random generator.

    Returns:
        Tuple ``(qber, remaining_alice, remaining_bob, sample_indices)``.
    """
    n = len(alice_sifted)
    sample_size = max(1, int(n * sample_fraction))
    sample_indices = rng.choice(n, size=sample_size, replace=False)
    sample_indices.sort()

    errors = int(np.sum(alice_sifted[sample_indices] != bob_sifted[sample_indices]))
    qber = errors / sample_size if sample_size > 0 else 0.0

    # Remove sampled positions
    keep_mask = np.ones(n, dtype=bool)
    keep_mask[sample_indices] = False
    return qber, alice_sifted[keep_mask], bob_sifted[keep_mask], sample_indices


# ── Error correction (simplified Cascade) ─────────────────────────────


def _cascade_pass(
    alice_bits: NDArray[np.uint8],
    bob_bits: NDArray[np.uint8],
    block_size: int,
) -> tuple[NDArray[np.uint8], int]:
    """Run one pass of Cascade error correction.

    Args:
        alice_bits: Alice's bits (reference).
        bob_bits: Bob's bits (to be corrected).
        block_size: Block size for this pass.

    Returns:
        Tuple ``(corrected_bob_bits, parity_bits_leaked)`` where
        *parity_bits_leaked* counts the number of parity checks
        revealed over the classical channel.
    """
    n = len(alice_bits)
    corrected = bob_bits.copy()
    leaked = 0

    for start in range(0, n, block_size):
        end = min(start + block_size, n)
        a_parity = int(np.sum(alice_bits[start:end])) % 2
        b_parity = int(np.sum(corrected[start:end])) % 2
        leaked += 1  # one parity bit exchanged per block

        if a_parity != b_parity:
            # Binary search for one error in this block
            lo, hi = start, end
            while hi - lo > 1:
                mid = (lo + hi) // 2
                a_par = int(np.sum(alice_bits[lo:mid])) % 2
                b_par = int(np.sum(corrected[lo:mid])) % 2
                leaked += 1
                if a_par != b_par:
                    hi = mid
                else:
                    lo = mid
            # Flip the identified error bit
            corrected[lo] ^= 1

    return corrected, leaked


def parity_error_correction(
    alice_bits: NDArray[np.uint8],
    bob_bits: NDArray[np.uint8],
    qber: float,
    rng: np.random.Generator,
    num_passes: int = 5,
    max_iterations: int = 4,
) -> tuple[NDArray[np.uint8], int]:
    """Simplified Cascade-style error correction.

    Runs *num_passes* passes with increasing block sizes and a random
    permutation per pass.  The whole procedure is repeated up to
    *max_iterations* times until no errors remain.

    Args:
        alice_bits: Alice's sifted key bits (reference).
        bob_bits: Bob's sifted key bits (to correct).
        qber: Estimated QBER (used to set initial block size).
        rng: NumPy random generator.
        num_passes: Number of Cascade passes per iteration.
        max_iterations: Maximum number of outer iterations.

    Returns:
        Tuple ``(corrected_bob_bits, total_leaked_bits)``.
    """
    n = len(alice_bits)
    if n == 0:
        return bob_bits.copy(), 0

    corrected = bob_bits.copy()
    total_leaked = 0

    for _iteration in range(max_iterations):
        # Initial block size ~ 0.73 / qber, clamped
        if qber > 0:
            block_size = max(2, min(n, int(0.73 / qber)))
        else:
            block_size = 16

        errors_before = int(np.sum(corrected != alice_bits))
        if errors_before == 0:
            break

        for pass_i in range(num_passes):
            perm = rng.permutation(n)
            inv_perm = np.argsort(perm)

            a_permuted = alice_bits[perm]
            b_permuted = corrected[perm]

            b_corrected_perm, leaked = _cascade_pass(a_permuted, b_permuted, block_size)
            total_leaked += leaked

            corrected = b_corrected_perm[inv_perm]
            block_size = min(n, block_size * 2)

    return corrected, total_leaked


# ── Key confirmation ──────────────────────────────────────────────────


def confirm_keys(
    alice_bits: NDArray[np.uint8],
    bob_bits: NDArray[np.uint8],
) -> bool:
    """Confirm that both parties' keys match by comparing SHA-256 hashes.

    Args:
        alice_bits: Alice's final bit array.
        bob_bits: Bob's final bit array.

    Returns:
        ``True`` if the SHA-256 hashes are identical.
    """
    ha = hashlib.sha256(np.packbits(alice_bits).tobytes()).digest()
    hb = hashlib.sha256(np.packbits(bob_bits).tobytes()).digest()
    return secrets.compare_digest(ha, hb)


# ── Privacy amplification (Toeplitz hashing) ──────────────────────────


def privacy_amplification(
    bits: NDArray[np.uint8],
    out_bits: int,
    leaked_bits: int,
    seed_bytes: bytes,
    security_margin: int = 64,
) -> bytes:
    """Compress the key via a Toeplitz-matrix universal hash over GF(2).

    The output length must satisfy
    ``out_bits <= len(bits) - leaked_bits - security_margin``.

    Args:
        bits: Input bit array.
        out_bits: Desired output length in bits.
        leaked_bits: Number of parity bits leaked during error correction.
        seed_bytes: Public random seed for the Toeplitz matrix.
        security_margin: Extra bits to discard for security.

    Returns:
        The privacy-amplified key as bytes.

    Raises:
        InsufficientKeyError: If the input is too short.
    """
    n = len(bits)
    max_out = n - leaked_bits - security_margin
    if out_bits > max_out:
        raise InsufficientKeyError(
            f"Cannot produce {out_bits} bits: input has {n} bits, "
            f"{leaked_bits} leaked, margin {security_margin} → "
            f"max output = {max_out}"
        )

    # Build Toeplitz matrix from seed
    # A Toeplitz matrix of size (out_bits × n) is defined by its first
    # row and first column, i.e. (out_bits + n - 1) bits.
    needed_bits = out_bits + n - 1
    seed_rng = np.random.Generator(np.random.PCG64(
        int.from_bytes(hashlib.sha256(seed_bytes).digest()[:16], "big")
    ))
    t_vec = seed_rng.integers(0, 2, size=needed_bits, dtype=np.uint8)

    # Matrix-vector product over GF(2) using NumPy
    # result[i] = sum(t_vec[i : i+n] * bits) mod 2
    result = np.zeros(out_bits, dtype=np.uint8)
    for i in range(out_bits):
        result[i] = np.bitwise_xor.reduce(
            np.bitwise_and(t_vec[i: i + n], bits)
        )

    return np.packbits(result).tobytes()[: (out_bits + 7) // 8]
