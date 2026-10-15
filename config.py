"""Central configuration for the hybrid QKD-PQC project."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def _project_root() -> Path:
    """Return the project root directory (where this file lives)."""
    return Path(__file__).resolve().parent


@dataclass
class Config:
    """Runtime configuration with sensible defaults.

    All paths are relative to the project root and created lazily.
    """

    # Networking
    HOST: str = "127.0.0.1"
    PORT: int = 9000

    # BB84 parameters
    N_QUBITS: int = 4096
    SAMPLE_FRACTION: float = 0.25
    QBER_THRESHOLD: float = 0.11
    CHANNEL_NOISE: float = 0.0
    FINAL_KEY_BITS: int = 256
    MIN_SIFTED_BITS: int = 256

    # PQC parameters
    MLKEM_LEVEL: int = 768

    # Key derivation
    HKDF_INFO: bytes = b"hybrid-qkd-pqc-v1"

    # Directories (resolved lazily via properties)
    _log_dir: Path = field(default_factory=lambda: _project_root() / "logs")
    _results_dir: Path = field(default_factory=lambda: _project_root() / "results")

    @property
    def LOG_DIR(self) -> Path:
        """Directory for session logs (created on first access)."""
        self._log_dir.mkdir(parents=True, exist_ok=True)
        return self._log_dir

    @property
    def RESULTS_DIR(self) -> Path:
        """Directory for benchmark results (created on first access)."""
        self._results_dir.mkdir(parents=True, exist_ok=True)
        return self._results_dir
