"""JSON-lines event logger for session tracing.

Writes structured events to ``logs/session_<timestamp>_<role>.jsonl``.
Never logs secret keys — only lengths, public-value hashes, timings,
and QBER.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from config import Config


class EventLog:
    """Structured JSON-lines session logger.

    Args:
        role: ``"client"`` or ``"server"``.
        config: Optional project configuration.
    """

    def __init__(self, role: str, config: Config | None = None) -> None:
        cfg = config or Config()
        ts = time.strftime("%Y%m%d_%H%M%S")
        self._path: Path = cfg.LOG_DIR / f"session_{ts}_{role}.jsonl"
        self.role = role
        self._entries: list[dict[str, Any]] = []

    @property
    def path(self) -> Path:
        """Path to the log file."""
        return self._path

    def log(self, event: str, **details: Any) -> None:
        """Append an event to the log.

        Args:
            event: Event name (e.g. ``"connected"``, ``"qber_measured"``).
            **details: Arbitrary key-value pairs (no secret keys!).
        """
        entry = {
            "ts": time.time(),
            "role": self.role,
            "event": event,
            "details": details,
        }
        self._entries.append(entry)

    def flush(self) -> None:
        """Write all buffered entries to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            for entry in self._entries:
                f.write(json.dumps(entry, default=str) + "\n")
        self._entries.clear()

    @property
    def entries(self) -> list[dict[str, Any]]:
        """Return all buffered entries (useful for tests)."""
        return list(self._entries)

    @staticmethod
    def read_log(path: Path) -> list[dict[str, Any]]:
        """Read a JSONL log file and return a list of entries.

        Args:
            path: Path to the ``.jsonl`` file.

        Returns:
            List of event dicts.
        """
        entries: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries
