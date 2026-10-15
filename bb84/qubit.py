"""Qubit representation and measurement for the BB84 simulation.

Provides both single-qubit and vectorised (NumPy) operations for
performance when simulating thousands of qubits.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

import numpy as np
from numpy.typing import NDArray


class Basis(IntEnum):
    """Measurement / preparation basis for a BB84 qubit."""

    RECTILINEAR = 0  # {|0⟩, |1⟩}
    DIAGONAL = 1     # {|+⟩, |−⟩}


@dataclass(frozen=True)
class Qubit:
    """A single prepared BB84 qubit.

    Attributes:
        basis: The basis in which the qubit was prepared.
        bit:   The classical bit value (0 or 1).
    """

    basis: Basis
    bit: int

    def __post_init__(self) -> None:
        if self.bit not in (0, 1):
            raise ValueError(f"bit must be 0 or 1, got {self.bit}")


def measure(qubit: Qubit, measure_basis: Basis,
            rng: np.random.Generator) -> tuple[int, Qubit]:
    """Measure a single qubit in the given basis.

    If *measure_basis* matches *qubit.basis* the outcome is deterministic
    (returns the stored bit).  Otherwise the outcome is uniformly random.
    The returned qubit is the post-measurement state (collapsed).

    Args:
        qubit: The qubit to measure.
        measure_basis: The basis to measure in.
        rng: NumPy random generator for the random outcome.

    Returns:
        A tuple ``(result_bit, collapsed_qubit)``.
    """
    if measure_basis == qubit.basis:
        result = qubit.bit
    else:
        result = int(rng.integers(0, 2))
    return result, Qubit(basis=measure_basis, bit=result)


# ── Vectorised helpers ────────────────────────────────────────────────


def measure_array(
    bases: NDArray[np.uint8],
    bits: NDArray[np.uint8],
    measure_bases: NDArray[np.uint8],
    rng: np.random.Generator,
) -> NDArray[np.uint8]:
    """Vectorised measurement of an array of qubits.

    Args:
        bases: Preparation bases (0 = rectilinear, 1 = diagonal).
        bits: Preparation bits.
        measure_bases: Measurement bases chosen by the receiver.
        rng: NumPy random generator.

    Returns:
        Array of measurement outcome bits (uint8).
    """
    n = len(bases)
    same = bases == measure_bases
    random_bits = rng.integers(0, 2, size=n, dtype=np.uint8)
    return np.where(same, bits, random_bits)
