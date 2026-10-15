"""End-to-end tests: server + client in-process on a random port."""

from __future__ import annotations

import socket
import threading
import time

import pytest

from config import Config
from network.server import HybridServer
from network.client import HybridClient


def _free_port() -> int:
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestHybridHandshake:
    """Full hybrid handshake: server and client derive the same key."""

    def test_hybrid_key_agreement(self) -> None:
        port = _free_port()
        cfg = Config()
        cfg.PORT = port
        cfg.N_QUBITS = 4096

        server = HybridServer(mode="hybrid", eve_rate=0.0, noise=0.0,
                               config=cfg, port_override=port)

        server_thread = threading.Thread(target=server.serve_one, daemon=True)
        server_thread.start()
        time.sleep(0.3)  # let server bind

        client = HybridClient(mode="hybrid", config=cfg)
        # Monkey-patch to avoid interactive input
        client._chat_loop = lambda *a, **kw: None  # type: ignore[assignment]
        # Also patch server chat loop
        HybridServer._chat_loop = lambda *a, **kw: None  # type: ignore[assignment]

        client.connect_and_run()
        server_thread.join(timeout=30)

        assert not client.aborted, f"Client aborted: {client.abort_reason}"
        assert client.session_key_hash is not None
        assert server.session_key_hash is not None
        assert client.session_key_hash == server.session_key_hash


class TestPQCOnly:
    """PQC-only mode handshake."""

    def test_pqc_only(self) -> None:
        port = _free_port()
        cfg = Config()
        cfg.PORT = port

        server = HybridServer(mode="pqc", config=cfg, port_override=port)
        HybridServer._chat_loop = lambda *a, **kw: None  # type: ignore[assignment]

        server_thread = threading.Thread(target=server.serve_one, daemon=True)
        server_thread.start()
        time.sleep(0.3)

        client = HybridClient(mode="pqc", config=cfg)
        client._chat_loop = lambda *a, **kw: None  # type: ignore[assignment]
        client.connect_and_run()
        server_thread.join(timeout=30)

        assert not client.aborted
        assert client.session_key_hash == server.session_key_hash


class TestEveAbort:
    """With full Eve, both sides should abort due to high QBER."""

    def test_eve_causes_abort(self) -> None:
        port = _free_port()
        cfg = Config()
        cfg.PORT = port
        cfg.N_QUBITS = 8192

        server = HybridServer(mode="hybrid", eve_rate=1.0, noise=0.0,
                               config=cfg, port_override=port)
        HybridServer._chat_loop = lambda *a, **kw: None  # type: ignore[assignment]

        server_thread = threading.Thread(target=server.serve_one, daemon=True)
        server_thread.start()
        time.sleep(0.3)

        client = HybridClient(mode="hybrid", config=cfg)
        client._chat_loop = lambda *a, **kw: None  # type: ignore[assignment]
        client.connect_and_run()
        server_thread.join(timeout=30)

        assert client.aborted
        assert "QBER" in (client.abort_reason or "")
