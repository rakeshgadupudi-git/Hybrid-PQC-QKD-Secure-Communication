"""ML-KEM (Kyber) key encapsulation wrapper.

Wraps the ``kyber-py`` library to provide a uniform interface for
ML-KEM-512, ML-KEM-768 and ML-KEM-1024 (FIPS 203).

.. warning::
    ``kyber-py`` is a pure-Python educational implementation.
    It is **not** constant-time and must not be used in production.
"""

from __future__ import annotations

from dataclasses import dataclass

from kyber_py.ml_kem import ML_KEM_512, ML_KEM_768, ML_KEM_1024


# Mapping from security level to kyber-py object
_LEVELS = {
    512: ML_KEM_512,
    768: ML_KEM_768,
    1024: ML_KEM_1024,
}


@dataclass(frozen=True)
class MLKEMSizes:
    """Byte sizes for ML-KEM artefacts at a given security level.

    Attributes:
        ek: Encapsulation (public) key size in bytes.
        dk: Decapsulation (secret) key size in bytes.
        ct: Ciphertext size in bytes.
        ss: Shared secret size in bytes (always 32).
    """

    ek: int
    dk: int
    ct: int
    ss: int


class MLKEMKeyExchange:
    """ML-KEM key encapsulation mechanism (FIPS 203).

    Args:
        level: Security parameter set — 512, 768, or 1024.

    Raises:
        ValueError: If *level* is not one of 512, 768, 1024.
    """

    def __init__(self, level: int = 768) -> None:
        if level not in _LEVELS:
            raise ValueError(
                f"Unsupported ML-KEM level {level}; choose from {sorted(_LEVELS)}"
            )
        self.level = level
        self._kem = _LEVELS[level]

    def generate_keypair(self) -> tuple[bytes, bytes]:
        """Generate an ML-KEM keypair.

        Returns:
            Tuple ``(encapsulation_key, decapsulation_key)``.
        """
        ek, dk = self._kem.keygen()
        return bytes(ek), bytes(dk)

    def encapsulate(self, ek: bytes) -> tuple[bytes, bytes]:
        """Encapsulate: produce a shared secret and ciphertext.

        Args:
            ek: Encapsulation (public) key.

        Returns:
            Tuple ``(shared_secret, ciphertext)``.
        """
        key, ct = self._kem.encaps(ek)
        return bytes(key), bytes(ct)

    def decapsulate(self, dk: bytes, ciphertext: bytes) -> bytes:
        """Decapsulate: recover the shared secret from a ciphertext.

        Args:
            dk: Decapsulation (secret) key.
            ciphertext: The ciphertext from :meth:`encapsulate`.

        Returns:
            The shared secret (32 bytes).
        """
        return bytes(self._kem.decaps(dk, ciphertext))

    def sizes(self) -> MLKEMSizes:
        """Return the byte sizes for this security level.

        Returns:
            An :class:`MLKEMSizes` instance.
        """
        ek, dk = self.generate_keypair()
        _, ct = self.encapsulate(ek)
        return MLKEMSizes(ek=len(ek), dk=len(dk), ct=len(ct), ss=32)
