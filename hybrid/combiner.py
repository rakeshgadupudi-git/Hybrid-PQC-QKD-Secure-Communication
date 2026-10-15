"""Hybrid key combiner using HKDF-SHA256.

Fuses independent secrets from QKD, PQC, and/or classical key exchange
into a single session key.  The session remains secure as long as
**at least one** component holds.
"""

from __future__ import annotations

import struct

from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from config import Config

# Supported modes and which secrets they require
_REQUIRED: dict[str, set[str]] = {
    "hybrid": {"qkd", "pqc"},
    "pqc": {"pqc"},
    "qkd": {"qkd"},
    "classical": {"classical"},
}


class HybridKeyCombiner:
    """Derive a single session key from multiple independent secrets.

    Secrets are concatenated in a fixed, length-prefixed order
    (QKD → PQC → classical) and then run through HKDF-SHA256.

    Args:
        mode: One of ``"hybrid"``, ``"pqc"``, ``"qkd"``, ``"classical"``.
        config: Optional project configuration.
    """

    MODES = frozenset(_REQUIRED)

    def __init__(self, mode: str = "hybrid", config: Config | None = None) -> None:
        if mode not in _REQUIRED:
            raise ValueError(
                f"Unknown mode '{mode}'; choose from {sorted(_REQUIRED)}"
            )
        self.mode = mode
        self._cfg = config or Config()

    @staticmethod
    def _len_prefix(data: bytes | None) -> bytes:
        """Return 4-byte big-endian length + data, or 4 zero bytes if None."""
        if data is None:
            return struct.pack(">I", 0)
        return struct.pack(">I", len(data)) + data

    def combine(
        self,
        qkd_key: bytes | None = None,
        pq_secret: bytes | None = None,
        classical_secret: bytes | None = None,
        transcript_hash: bytes = b"",
    ) -> bytes:
        """Derive a 256-bit session key from available secrets.

        Args:
            qkd_key: BB84-derived key (required for ``hybrid`` / ``qkd``).
            pq_secret: ML-KEM shared secret (required for ``hybrid`` / ``pqc``).
            classical_secret: X25519 shared secret (required for ``classical``).
            transcript_hash: SHA-256 hash of the handshake transcript (used as
                HKDF salt for channel binding).

        Returns:
            32-byte session key.

        Raises:
            ValueError: If a required secret is missing for the chosen mode.
        """
        required = _REQUIRED[self.mode]
        provided = set()
        if qkd_key is not None:
            provided.add("qkd")
        if pq_secret is not None:
            provided.add("pqc")
        if classical_secret is not None:
            provided.add("classical")

        missing = required - provided
        if missing:
            raise ValueError(
                f"Mode '{self.mode}' requires {sorted(required)}, "
                f"but missing: {sorted(missing)}"
            )

        # Fixed concatenation order: QKD → PQC → classical
        ikm = (
            self._len_prefix(qkd_key)
            + self._len_prefix(pq_secret)
            + self._len_prefix(classical_secret)
        )

        hkdf = HKDF(
            algorithm=SHA256(),
            length=32,
            salt=transcript_hash if transcript_hash else None,
            info=self._cfg.HKDF_INFO,
        )
        return hkdf.derive(ikm)
