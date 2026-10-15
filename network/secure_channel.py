"""AES-256-GCM secure channel with per-direction counter nonces.

The nonce layout (96 bits total):
    ┌──────────────┬──────────────────────┐
    │ direction(4B)│   counter (8B)       │
    └──────────────┴──────────────────────┘

The direction prefix is ``0x00000000`` for client→server and
``0x00000001`` for server→client, ensuring unique nonces even if both
sides use the same session key.

The sequence number is included as authenticated-but-unencrypted
associated data (AAD) so replays and reordering are detected.
"""

from __future__ import annotations

import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SecureChannelError(Exception):
    """Raised on tamper detection, replay, or wrong-direction nonce."""


class SecureChannel:
    """AES-256-GCM encrypted channel.

    Args:
        session_key: 32-byte session key.
        role: ``"client"`` or ``"server"``.

    Raises:
        ValueError: If *session_key* is not 32 bytes or *role* is invalid.
    """

    _DIRECTION = {"client": b"\x00\x00\x00\x00", "server": b"\x00\x00\x00\x01"}

    def __init__(self, session_key: bytes, role: str) -> None:
        if len(session_key) != 32:
            raise ValueError(f"Session key must be 32 bytes, got {len(session_key)}")
        if role not in self._DIRECTION:
            raise ValueError(f"role must be 'client' or 'server', got '{role}'")
        self._aes = AESGCM(session_key)
        self._send_prefix = self._DIRECTION[role]
        self._recv_prefix = self._DIRECTION["server" if role == "client" else "client"]
        self._send_counter: int = 0
        self._recv_counter: int = 0

    def _make_nonce(self, prefix: bytes, counter: int) -> bytes:
        return prefix + struct.pack(">Q", counter)

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt a plaintext message.

        Args:
            plaintext: The data to encrypt.

        Returns:
            ``nonce (12B) || ciphertext+tag``.
        """
        nonce = self._make_nonce(self._send_prefix, self._send_counter)
        aad = struct.pack(">Q", self._send_counter)
        ct = self._aes.encrypt(nonce, plaintext, aad)
        self._send_counter += 1
        return nonce + ct

    def decrypt(self, blob: bytes) -> bytes:
        """Decrypt and verify a received message.

        Args:
            blob: ``nonce (12B) || ciphertext+tag`` as returned by
                :meth:`encrypt` on the peer.

        Returns:
            The decrypted plaintext.

        Raises:
            SecureChannelError: On tamper, replay, or wrong-direction nonce.
        """
        if len(blob) < 12:
            raise SecureChannelError("Message too short")

        nonce = blob[:12]
        ct = blob[12:]

        # Verify direction prefix
        prefix = nonce[:4]
        if prefix != self._recv_prefix:
            raise SecureChannelError(
                f"Wrong direction prefix: expected {self._recv_prefix!r}, got {prefix!r}"
            )

        # Extract counter from nonce
        (counter,) = struct.unpack(">Q", nonce[4:])
        if counter != self._recv_counter:
            raise SecureChannelError(
                f"Replay/reorder: expected counter {self._recv_counter}, got {counter}"
            )

        aad = struct.pack(">Q", counter)
        try:
            pt = self._aes.decrypt(nonce, ct, aad)
        except Exception as exc:
            raise SecureChannelError(f"Decryption failed (tamper?): {exc}") from exc

        self._recv_counter += 1
        return pt
