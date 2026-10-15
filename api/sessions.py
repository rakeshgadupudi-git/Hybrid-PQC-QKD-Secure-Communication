"""In-memory session store for chat and attack demos.

Each session holds a real SecureChannel pair from a real handshake.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from network.secure_channel import SecureChannel


@dataclass
class ChatSession:
    """A live chat session between Alice and Bob."""

    session_id: str
    alice_channel: SecureChannel
    bob_channel: SecureChannel
    session_fingerprint: str
    mode: str
    messages: list[dict[str, Any]] = field(default_factory=list)


# Global session store
_sessions: dict[str, ChatSession] = {}


def create_session(
    session_key: bytes,
    session_fingerprint: str,
    mode: str,
) -> ChatSession:
    """Create a new chat session with a real SecureChannel pair."""
    sid = uuid.uuid4().hex[:12]
    session = ChatSession(
        session_id=sid,
        alice_channel=SecureChannel(session_key, "client"),
        bob_channel=SecureChannel(session_key, "server"),
        session_fingerprint=session_fingerprint,
        mode=mode,
    )
    _sessions[sid] = session
    return session


def get_session(session_id: str) -> ChatSession | None:
    """Retrieve a session by ID."""
    return _sessions.get(session_id)


def clear_sessions() -> None:
    """Clear all sessions (for testing)."""
    _sessions.clear()
