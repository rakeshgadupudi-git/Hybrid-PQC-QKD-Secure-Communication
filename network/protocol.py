"""Length-prefixed JSON protocol framing for the hybrid handshake.

Wire format: 4-byte big-endian length + UTF-8 JSON payload.
"""

from __future__ import annotations

import json
import socket
import struct
from enum import Enum
from typing import Any


MAX_MSG_SIZE = 8 * 1024 * 1024  # 8 MB


class MessageType(str, Enum):
    """All message types used during the hybrid handshake and chat."""

    HELLO = "HELLO"
    BB84_QUBITS = "BB84_QUBITS"
    BB84_BASES = "BB84_BASES"
    BB84_BASES_MATCH = "BB84_BASES_MATCH"
    BB84_SAMPLE = "BB84_SAMPLE"
    BB84_SAMPLE_REPLY = "BB84_SAMPLE_REPLY"
    BB84_EC_PARITY = "BB84_EC_PARITY"
    BB84_CONFIRM = "BB84_CONFIRM"
    BB84_PA_SEED = "BB84_PA_SEED"
    PQC_PUBLIC_KEY = "PQC_PUBLIC_KEY"
    PQC_CIPHERTEXT = "PQC_CIPHERTEXT"
    KEY_CONFIRM = "KEY_CONFIRM"
    CHAT = "CHAT"
    ABORT = "ABORT"
    BYE = "BYE"


class ProtocolError(Exception):
    """Raised on framing or protocol violations."""


def _recvall(sock: socket.socket, n: int) -> bytes:
    """Receive exactly *n* bytes from *sock*."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket closed while receiving data")
        buf.extend(chunk)
    return bytes(buf)


def send_msg(sock: socket.socket, msg_type: MessageType | str, payload: dict[str, Any] | None = None) -> bytes:
    """Send a framed JSON message and return the raw bytes sent.

    Args:
        sock: Connected socket.
        msg_type: The message type tag.
        payload: Optional JSON-serialisable payload dict.

    Returns:
        The raw bytes that were sent (for transcript hashing).
    """
    msg: dict[str, Any] = {"type": msg_type.value if isinstance(msg_type, MessageType) else str(msg_type)}
    if payload is not None:
        msg["payload"] = payload
    data = json.dumps(msg, separators=(",", ":")).encode("utf-8")
    if len(data) > MAX_MSG_SIZE:
        raise ProtocolError(f"Message too large: {len(data)} > {MAX_MSG_SIZE}")
    header = struct.pack(">I", len(data))
    sock.sendall(header + data)
    return header + data


def recv_msg(sock: socket.socket) -> tuple[MessageType, dict[str, Any], bytes]:
    """Receive a framed JSON message.

    Args:
        sock: Connected socket.

    Returns:
        Tuple ``(msg_type, payload, raw_bytes)`` where *raw_bytes*
        is the complete frame (header + body) for transcript hashing.

    Raises:
        ProtocolError: On framing violations or oversized messages.
        ConnectionError: If the socket is closed.
    """
    header = _recvall(sock, 4)
    (length,) = struct.unpack(">I", header)
    if length > MAX_MSG_SIZE:
        raise ProtocolError(f"Message too large: {length} > {MAX_MSG_SIZE}")
    body = _recvall(sock, length)
    raw = header + body
    try:
        msg = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ProtocolError(f"Invalid JSON: {exc}") from exc
    msg_type = MessageType(msg["type"])
    payload = msg.get("payload", {})
    return msg_type, payload, raw
