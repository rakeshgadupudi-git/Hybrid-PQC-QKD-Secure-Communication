"""Eavesdropper (Eve) simulation for the BB84 protocol.

Eve performs an intercept-resend attack: she measures each intercepted
qubit in a random basis and resends a new qubit prepared in that basis
with her measurement result.
"""

from __future__ import annotations

import numpy as np

from bb84.qubit import measure_array


class Eavesdropper:
    """Simulated eavesdropper on a BB84 quantum channel.

    Args:
        intercept_rate: Probability of intercepting each qubit (0.0–1.0).
        rng: NumPy random generator.
    """

    def __init__(
        self,
        intercept_rate: float = 1.0,
        rng: np.random.Generator | None = None,
    ) -> None:
        if not 0.0 <= intercept_rate <= 1.0:
            raise ValueError(f"intercept_rate must be in [0, 1], got {intercept_rate}")
        self.intercept_rate = intercept_rate
        self._rng = rng or np.random.default_rng()
        self.intercepted_count: int = 0

    def intercept_resend(self, batch: "QubitBatch") -> "QubitBatch":  # noqa: F821
        """Perform an intercept-resend attack on a qubit batch.

        For each qubit chosen for interception (with probability
        ``intercept_rate``), Eve measures in a random basis and resends
        a new qubit prepared in that basis with her measurement result.

        Args:
            batch: The qubit batch transiting the quantum channel.

        Returns:
            The (possibly disturbed) ``QubitBatch``.
        """
        from bb84.simulator import QubitBatch  # avoid circular import

        n = len(batch)
        bases = batch.bases.copy()
        bits = batch.bits.copy()

        # Determine which qubits Eve intercepts
        intercept_mask = self._rng.random(n) < self.intercept_rate
        self.intercepted_count = int(np.sum(intercept_mask))

        if self.intercepted_count == 0:
            return QubitBatch(bases=bases, bits=bits)

        # Eve chooses random bases for the intercepted qubits
        eve_bases = self._rng.integers(0, 2, size=n, dtype=np.uint8)

        # Eve measures only the intercepted qubits
        eve_results = measure_array(
            bases[intercept_mask],
            bits[intercept_mask],
            eve_bases[intercept_mask],
            self._rng,
        )

        # Eve resends: replace the intercepted qubits with her
        # measurement basis and result
        bases[intercept_mask] = eve_bases[intercept_mask]
        bits[intercept_mask] = eve_results

        return QubitBatch(bases=bases, bits=bits)
