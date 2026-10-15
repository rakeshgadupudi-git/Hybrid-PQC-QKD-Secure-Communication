"""Tests for the hybrid key combiner."""

from __future__ import annotations

import pytest

from hybrid.combiner import HybridKeyCombiner


class TestDeterminism:
    """Same inputs must always produce the same session key."""

    def test_deterministic(self) -> None:
        combiner = HybridKeyCombiner(mode="hybrid")
        qkd = b"\x01" * 32
        pqc = b"\x02" * 32
        th = b"\xAA" * 32
        k1 = combiner.combine(qkd_key=qkd, pq_secret=pqc, transcript_hash=th)
        k2 = combiner.combine(qkd_key=qkd, pq_secret=pqc, transcript_hash=th)
        assert k1 == k2
        assert len(k1) == 32


class TestDifferentInputs:
    """Changing any component must change the output."""

    def test_different_qkd_changes_output(self) -> None:
        combiner = HybridKeyCombiner(mode="hybrid")
        pqc = b"\x02" * 32
        th = b"\xAA" * 32
        k1 = combiner.combine(qkd_key=b"\x01" * 32, pq_secret=pqc, transcript_hash=th)
        k2 = combiner.combine(qkd_key=b"\xFF" * 32, pq_secret=pqc, transcript_hash=th)
        assert k1 != k2

    def test_different_pqc_changes_output(self) -> None:
        combiner = HybridKeyCombiner(mode="hybrid")
        qkd = b"\x01" * 32
        th = b"\xAA" * 32
        k1 = combiner.combine(qkd_key=qkd, pq_secret=b"\x02" * 32, transcript_hash=th)
        k2 = combiner.combine(qkd_key=qkd, pq_secret=b"\xFF" * 32, transcript_hash=th)
        assert k1 != k2


class TestMissingSecret:
    """Hybrid mode must raise ValueError when a required secret is missing."""

    def test_missing_qkd_in_hybrid(self) -> None:
        combiner = HybridKeyCombiner(mode="hybrid")
        with pytest.raises(ValueError, match="missing"):
            combiner.combine(pq_secret=b"\x02" * 32, transcript_hash=b"h")

    def test_missing_pqc_in_hybrid(self) -> None:
        combiner = HybridKeyCombiner(mode="hybrid")
        with pytest.raises(ValueError, match="missing"):
            combiner.combine(qkd_key=b"\x01" * 32, transcript_hash=b"h")


class TestModes:
    """Each mode should work when given the right secrets."""

    def test_pqc_only(self) -> None:
        c = HybridKeyCombiner(mode="pqc")
        k = c.combine(pq_secret=b"\x02" * 32, transcript_hash=b"h")
        assert len(k) == 32

    def test_qkd_only(self) -> None:
        c = HybridKeyCombiner(mode="qkd")
        k = c.combine(qkd_key=b"\x01" * 32, transcript_hash=b"h")
        assert len(k) == 32

    def test_classical_only(self) -> None:
        c = HybridKeyCombiner(mode="classical")
        k = c.combine(classical_secret=b"\x03" * 32, transcript_hash=b"h")
        assert len(k) == 32

    def test_invalid_mode(self) -> None:
        with pytest.raises(ValueError):
            HybridKeyCombiner(mode="quantum-magic")
