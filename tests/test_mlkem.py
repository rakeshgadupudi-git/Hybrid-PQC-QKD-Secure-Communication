"""Tests for the ML-KEM (Kyber) key encapsulation module."""

from __future__ import annotations

import pytest

from pqc.mlkem import MLKEMKeyExchange


class TestMLKEMRoundTrip:
    """Verify that encaps → decaps recovers the same shared secret."""

    @pytest.mark.parametrize("level", [512, 768, 1024])
    def test_roundtrip(self, level: int) -> None:
        kem = MLKEMKeyExchange(level=level)
        ek, dk = kem.generate_keypair()
        shared, ct = kem.encapsulate(ek)
        recovered = kem.decapsulate(dk, ct)
        assert shared == recovered


class TestMLKEMTamper:
    """Tampering with the ciphertext should produce a different secret."""

    def test_tampered_ciphertext(self) -> None:
        kem = MLKEMKeyExchange(level=768)
        ek, dk = kem.generate_keypair()
        shared, ct = kem.encapsulate(ek)

        # Flip one byte in the ciphertext
        tampered = bytearray(ct)
        tampered[0] ^= 0xFF
        recovered = kem.decapsulate(dk, bytes(tampered))
        assert shared != recovered


class TestMLKEMSizes:
    """Verify key and ciphertext sizes match FIPS 203."""

    def test_768_sizes(self) -> None:
        kem = MLKEMKeyExchange(level=768)
        s = kem.sizes()
        assert s.ek == 1184, f"ek size: {s.ek}"
        assert s.ct == 1088, f"ct size: {s.ct}"
        assert s.ss == 32, f"ss size: {s.ss}"

    def test_512_sizes(self) -> None:
        kem = MLKEMKeyExchange(level=512)
        s = kem.sizes()
        assert s.ek == 800
        assert s.ct == 768
        assert s.ss == 32

    def test_1024_sizes(self) -> None:
        kem = MLKEMKeyExchange(level=1024)
        s = kem.sizes()
        assert s.ek == 1568
        assert s.ct == 1568
        assert s.ss == 32


class TestMLKEMInvalidLevel:
    """Invalid security level should raise ValueError."""

    def test_bad_level(self) -> None:
        with pytest.raises(ValueError):
            MLKEMKeyExchange(level=256)
