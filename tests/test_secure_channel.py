"""Tests for the AES-256-GCM secure channel."""

from __future__ import annotations

import os

import pytest

from network.secure_channel import SecureChannel, SecureChannelError


class TestRoundTrip:
    """Basic encrypt/decrypt cycle."""

    def test_roundtrip(self) -> None:
        key = os.urandom(32)
        client_ch = SecureChannel(key, "client")
        server_ch = SecureChannel(key, "server")

        plaintext = b"Hello, quantum world!"
        ct = client_ch.encrypt(plaintext)
        pt = server_ch.decrypt(ct)
        assert pt == plaintext

    def test_multiple_messages(self) -> None:
        key = os.urandom(32)
        client_ch = SecureChannel(key, "client")
        server_ch = SecureChannel(key, "server")

        for i in range(10):
            msg = f"Message {i}".encode()
            ct = client_ch.encrypt(msg)
            pt = server_ch.decrypt(ct)
            assert pt == msg


class TestTamperDetection:
    """Flipping bits in the ciphertext must be detected."""

    def test_tampered_ciphertext(self) -> None:
        key = os.urandom(32)
        client_ch = SecureChannel(key, "client")
        server_ch = SecureChannel(key, "server")

        ct = client_ch.encrypt(b"secret data")
        tampered = bytearray(ct)
        tampered[-1] ^= 0xFF
        with pytest.raises(SecureChannelError, match="tamper"):
            server_ch.decrypt(bytes(tampered))


class TestReplayRejection:
    """Replaying a message must be detected."""

    def test_replay(self) -> None:
        key = os.urandom(32)
        client_ch = SecureChannel(key, "client")
        server_ch = SecureChannel(key, "server")

        ct = client_ch.encrypt(b"message 1")
        server_ch.decrypt(ct)  # first time OK

        # Second send to advance client counter
        ct2 = client_ch.encrypt(b"message 2")

        # Try to replay ct (counter 0 when expecting 1)
        with pytest.raises(SecureChannelError, match="Replay"):
            server_ch.decrypt(ct)


class TestWrongDirection:
    """Messages with wrong direction prefix must be rejected."""

    def test_wrong_direction(self) -> None:
        key = os.urandom(32)
        server_ch1 = SecureChannel(key, "server")
        server_ch2 = SecureChannel(key, "server")

        # server encrypts with server prefix
        ct = server_ch1.encrypt(b"data")
        # another server instance tries to decrypt — expects client prefix
        with pytest.raises(SecureChannelError, match="direction"):
            server_ch2.decrypt(ct)


class TestInvalidKeySize:
    """Wrong key size must raise ValueError."""

    def test_short_key(self) -> None:
        with pytest.raises(ValueError):
            SecureChannel(b"short", "client")
