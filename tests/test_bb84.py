"""Tests for the BB84 simulation modules."""

from __future__ import annotations

import numpy as np
import pytest

from bb84.postprocessing import (
    InsufficientKeyError,
    estimate_qber,
    parity_error_correction,
    privacy_amplification,
    sift_keys,
)
from bb84.session import BB84Result, run_bb84_local


class TestNoEveNoNoise:
    """BB84 with a clean channel: QBER should be 0, keys must match."""

    def test_qber_zero_and_accepted(self) -> None:
        result = run_bb84_local(n_qubits=4096, eve_rate=0.0, noise=0.0, seed=42)
        assert result.accepted, f"Aborted: {result.aborted_reason}"
        assert result.qber == 0.0
        assert result.final_key is not None
        assert len(result.final_key) > 0

    def test_sifted_length_about_half(self) -> None:
        result = run_bb84_local(n_qubits=10000, eve_rate=0.0, noise=0.0, seed=7)
        # Sifted ≈ n/2 ± some variance
        assert 0.40 * 10000 <= result.sifted_len <= 0.60 * 10000


class TestFullEve:
    """Eve intercepts every qubit → QBER ≈ 25%, session aborts."""

    def test_full_eve_qber_and_abort(self) -> None:
        result = run_bb84_local(n_qubits=20000, eve_rate=1.0, noise=0.0, seed=99)
        assert not result.accepted
        assert abs(result.qber - 0.25) < 0.03, f"QBER={result.qber}"
        assert result.eve_intercepted > 0

    def test_half_eve_qber(self) -> None:
        result = run_bb84_local(n_qubits=20000, eve_rate=0.5, noise=0.0, seed=101)
        expected = 0.125
        assert abs(result.qber - expected) < 0.03, f"QBER={result.qber}"


class TestLowNoise:
    """Low channel noise should still produce matching keys after EC."""

    def test_noise_002_keys_match(self) -> None:
        result = run_bb84_local(n_qubits=8192, eve_rate=0.0, noise=0.02, seed=55)
        assert result.accepted, f"Aborted: {result.aborted_reason}"
        assert result.final_key is not None


class TestSifting:
    """Unit tests for the sifting function."""

    def test_sift_keeps_matching_bases(self) -> None:
        alice_bases = np.array([0, 1, 0, 1, 0], dtype=np.uint8)
        bob_bases = np.array([0, 0, 0, 1, 1], dtype=np.uint8)
        alice_bits = np.array([1, 0, 1, 1, 0], dtype=np.uint8)
        bob_bits = np.array([1, 1, 1, 1, 0], dtype=np.uint8)
        a_s, b_s, idx = sift_keys(alice_bases, bob_bases, alice_bits, bob_bits)
        assert list(idx) == [0, 2, 3]
        np.testing.assert_array_equal(a_s, [1, 1, 1])
        np.testing.assert_array_equal(b_s, [1, 1, 1])


class TestPrivacyAmplification:
    """Unit tests for privacy amplification output sizes."""

    def test_output_length(self) -> None:
        rng = np.random.default_rng(42)
        bits = rng.integers(0, 2, size=1024, dtype=np.uint8)
        key = privacy_amplification(bits, out_bits=128, leaked_bits=10, seed_bytes=b"seed")
        assert len(key) == 16  # 128 bits = 16 bytes

    def test_insufficient_raises(self) -> None:
        bits = np.ones(100, dtype=np.uint8)
        with pytest.raises(InsufficientKeyError):
            privacy_amplification(bits, out_bits=100, leaked_bits=50, seed_bytes=b"x")
