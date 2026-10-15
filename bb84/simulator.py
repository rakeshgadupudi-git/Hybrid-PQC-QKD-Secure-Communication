"""BB84 protocol participants and quantum channel simulation.

Provides Alice (prepare), Bob (measure), a quantum channel with
optional noise and eavesdropping, and a ``QubitBatch`` container
for efficient wire transfer of qubit arrays.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from bb84.eve import Eavesdropper
from bb84.qubit import measure_array


@dataclass
class QubitBatch:
    """Container for a batch of qubits stored as NumPy uint8 arrays.

    Attributes:
        bases: Preparation bases (0 = rectilinear, 1 = diagonal).
        bits:  Classical bit values.
    """

    bases: NDArray[np.uint8]
    bits: NDArray[np.uint8]

    def __len__(self) -> int:
        return len(self.bases)

    # ── Wire format ───────────────────────────────────────────────────

    def to_wire(self) -> dict[str, str]:
        """Serialise to a JSON-friendly dict using packbits + base64.

        Returns:
            Dict with keys ``bases_b64``, ``bits_b64`` and ``n``.
        """
        return {
            "bases_b64": base64.b64encode(
                np.packbits(self.bases).tobytes()
            ).decode(),
            "bits_b64": base64.b64encode(
                np.packbits(self.bits).tobytes()
            ).decode(),
            "n": len(self.bases),
        }

    @classmethod
    def from_wire(cls, data: dict[str, str]) -> "QubitBatch":
        """Deserialise from a dict produced by :meth:`to_wire`.

        Args:
            data: Wire-format dict.

        Returns:
            Reconstructed ``QubitBatch``.
        """
        n: int = int(data["n"])
        bases = np.unpackbits(
            np.frombuffer(base64.b64decode(data["bases_b64"]), dtype=np.uint8)
        )[:n].copy()
        bits = np.unpackbits(
            np.frombuffer(base64.b64decode(data["bits_b64"]), dtype=np.uint8)
        )[:n].copy()
        return cls(bases=bases, bits=bits)


class BB84Alice:
    """Alice's side of the BB84 protocol: prepare qubits.

    Args:
        rng: NumPy random generator (seeded for reproducibility in tests).
    """

    def __init__(self, rng: np.random.Generator | None = None) -> None:
        self._rng = rng or np.random.default_rng()
        self.bits: NDArray[np.uint8] | None = None
        self.bases: NDArray[np.uint8] | None = None

    def prepare(self, n: int) -> QubitBatch:
        """Prepare *n* random BB84 qubits.

        Random bits and random bases are generated and stored internally
        so Alice can later participate in sifting and QBER estimation.

        Args:
            n: Number of qubits to prepare.

        Returns:
            A ``QubitBatch`` ready for transmission.
        """
        self.bits = self._rng.integers(0, 2, size=n, dtype=np.uint8)
        self.bases = self._rng.integers(0, 2, size=n, dtype=np.uint8)
        return QubitBatch(bases=self.bases.copy(), bits=self.bits.copy())


class BB84Bob:
    """Bob's side of the BB84 protocol: measure received qubits.

    Args:
        rng: NumPy random generator.
    """

    def __init__(self, rng: np.random.Generator | None = None) -> None:
        self._rng = rng or np.random.default_rng()
        self.bases: NDArray[np.uint8] | None = None
        self.bits: NDArray[np.uint8] | None = None

    def measure(self, batch: QubitBatch) -> tuple[NDArray[np.uint8], NDArray[np.uint8]]:
        """Measure a ``QubitBatch`` in randomly chosen bases.

        Args:
            batch: The received qubit batch.

        Returns:
            Tuple ``(measured_bits, measurement_bases)``.
        """
        n = len(batch)
        self.bases = self._rng.integers(0, 2, size=n, dtype=np.uint8)
        self.bits = measure_array(batch.bases, batch.bits, self.bases, self._rng)
        return self.bits.copy(), self.bases.copy()


class QuantumChannel:
    """Simulated quantum channel with optional noise and eavesdropper.

    Args:
        noise: Probability of a random bit-flip on each qubit.
        eavesdropper: An optional :class:`Eavesdropper` instance.
        rng: NumPy random generator.
    """

    def __init__(
        self,
        noise: float = 0.0,
        eavesdropper: Eavesdropper | None = None,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.noise = noise
        self.eavesdropper = eavesdropper
        self._rng = rng or np.random.default_rng()

    def transmit(self, batch: QubitBatch) -> QubitBatch:
        """Transmit a qubit batch through the channel.

        Applies eavesdropping first (if configured), then channel noise.

        Args:
            batch: The qubit batch to transmit.

        Returns:
            Possibly-disturbed ``QubitBatch``.
        """
        # Make copies so we don't mutate the sender's arrays
        bases = batch.bases.copy()
        bits = batch.bits.copy()

        # Eavesdropper intercept-resend
        if self.eavesdropper is not None:
            intercepted = QubitBatch(bases=bases, bits=bits)
            intercepted = self.eavesdropper.intercept_resend(intercepted)
            bases = intercepted.bases
            bits = intercepted.bits

        # Channel noise (random bit-flips)
        if self.noise > 0.0:
            flip_mask = self._rng.random(len(bits)) < self.noise
            bits[flip_mask] ^= 1

        return QubitBatch(bases=bases, bits=bits)
