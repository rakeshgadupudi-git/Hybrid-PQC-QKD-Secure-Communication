"""Bob (server) for the hybrid QKD-PQC secure communication protocol.

Listens on localhost, performs the hybrid handshake (BB84 + ML-KEM),
derives a session key, then enters an encrypted chat loop.

CLI usage::

    python -m network.server --mode hybrid --eve-rate 0.0 --noise 0.0
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import os
import socket
import sys
import threading
import time
from typing import Any

import numpy as np

from bb84.eve import Eavesdropper
from bb84.postprocessing import (
    InsufficientKeyError,
    confirm_keys,
    estimate_qber,
    parity_error_correction,
    privacy_amplification,
    sift_keys,
)
from bb84.qubit import measure_array
from bb84.simulator import BB84Bob, QubitBatch, QuantumChannel
from classical.ecdh import X25519KeyExchange
from config import Config
from hybrid.combiner import HybridKeyCombiner
from network.event_log import EventLog
from network.protocol import MessageType, ProtocolError, recv_msg, send_msg
from network.secure_channel import SecureChannel
from pqc.mlkem import MLKEMKeyExchange


class HybridServer:
    """Bob's side of the hybrid handshake protocol.

    Args:
        mode: Handshake mode — ``"hybrid"``, ``"pqc"``, ``"qkd"``, ``"classical"``.
        eve_rate: Eve intercept rate for the simulated quantum channel.
        noise: Channel noise probability.
        config: Project configuration.
        port_override: Override the port (useful for tests).
    """

    def __init__(
        self,
        mode: str = "hybrid",
        eve_rate: float = 0.0,
        noise: float = 0.0,
        config: Config | None = None,
        port_override: int | None = None,
        n_qubits: int | None = None,
    ) -> None:
        self.mode = mode
        self.eve_rate = eve_rate
        self.noise = noise
        self.cfg = config or Config()
        if port_override is not None:
            self.cfg.PORT = port_override
        if n_qubits is not None:
            self.cfg.N_QUBITS = n_qubits
        self._stop = threading.Event()
        self._server_sock: socket.socket | None = None
        # Exposed for testing
        self.session_key_hash: str | None = None

    def stop(self) -> None:
        """Signal the server to stop accepting connections."""
        self._stop.set()
        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass

    def serve_forever(self) -> None:
        """Listen for connections and handle one client at a time."""
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.settimeout(1.0)
        self._server_sock.bind((self.cfg.HOST, self.cfg.PORT))
        self._server_sock.listen(1)
        print(f"[Server] Listening on {self.cfg.HOST}:{self.cfg.PORT} mode={self.mode}")

        while not self._stop.is_set():
            try:
                conn, addr = self._server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            print(f"[Server] Connection from {addr}")
            try:
                self._handle_client(conn)
            except (ConnectionError, ProtocolError, OSError) as exc:
                print(f"[Server] Connection error: {exc}")
            finally:
                conn.close()
        print("[Server] Stopped.")

    def serve_one(self) -> None:
        """Accept and handle exactly one client, then return.

        Useful for tests.
        """
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((self.cfg.HOST, self.cfg.PORT))
        self._server_sock.listen(1)
        self._server_sock.settimeout(30.0)
        conn, _ = self._server_sock.accept()
        try:
            self._handle_client(conn)
        finally:
            conn.close()
            self._server_sock.close()

    def _handle_client(self, conn: socket.socket) -> None:
        """Run the full handshake and chat with one client."""
        log = EventLog("server", self.cfg)
        transcript: list[bytes] = []
        rng = np.random.default_rng()

        def _send(mt: MessageType, payload: dict[str, Any] | None = None) -> None:
            raw = send_msg(conn, mt, payload)
            transcript.append(raw)

        def _recv() -> tuple[MessageType, dict[str, Any]]:
            mt, pl, raw = recv_msg(conn)
            transcript.append(raw)
            return mt, pl

        # ── HELLO ─────────────────────────────────────────────────────
        log.log("connected")
        _send(MessageType.HELLO, {"mode": self.mode, "role": "server"})
        mt, pl = _recv()
        assert mt == MessageType.HELLO, f"Expected HELLO, got {mt}"
        log.log("hello_exchanged", peer_mode=pl.get("mode"))

        qkd_key: bytes | None = None
        pq_secret: bytes | None = None
        classical_secret: bytes | None = None

        # ── BB84 phase ────────────────────────────────────────────────
        if self.mode in ("hybrid", "qkd"):
            t0 = time.perf_counter()
            log.log("bb84_started", n_qubits=self.cfg.N_QUBITS)

            # Receive qubits from Alice
            mt, pl = _recv()
            assert mt == MessageType.BB84_QUBITS
            batch = QubitBatch.from_wire(pl)
            n_qubits = len(batch)

            # Pass through quantum channel (Eve + noise)
            eve = Eavesdropper(self.eve_rate, rng) if self.eve_rate > 0 else None
            channel = QuantumChannel(self.noise, eve, rng)
            batch = channel.transmit(batch)

            # Bob measures
            bob = BB84Bob(rng=rng)
            bob_bits, bob_bases = bob.measure(batch)

            # Exchange bases
            _send(MessageType.BB84_BASES, {
                "bases_b64": base64.b64encode(np.packbits(bob_bases).tobytes()).decode(),
                "n": int(len(bob_bases)),
            })
            mt, pl = _recv()
            assert mt == MessageType.BB84_BASES
            alice_bases = np.unpackbits(
                np.frombuffer(base64.b64decode(pl["bases_b64"]), dtype=np.uint8)
            )[:int(pl["n"])].copy()

            # Sift
            alice_sifted_placeholder = np.zeros(0, dtype=np.uint8)
            _, bob_sifted, kept = sift_keys(alice_bases, bob_bases, np.zeros_like(alice_bases), bob_bits)
            bob_sifted = bob_bits[kept]

            # Tell client which indices were kept
            _send(MessageType.BB84_BASES_MATCH, {
                "kept_b64": base64.b64encode(np.packbits(alice_bases == bob_bases).tobytes()).decode(),
                "n": int(len(alice_bases)),
                "sifted_len": int(len(bob_sifted)),
            })

            # Receive QBER sample request
            mt, pl = _recv()
            assert mt == MessageType.BB84_SAMPLE
            sample_indices = np.array(pl["indices"], dtype=np.intp)
            bob_sample = bob_sifted[sample_indices].tolist()
            _send(MessageType.BB84_SAMPLE_REPLY, {"bits": bob_sample})

            # Receive QBER result and Alice's remaining indices
            mt, pl = _recv()
            if mt == MessageType.ABORT:
                log.log("aborted", reason=pl.get("reason", "QBER too high"))
                log.flush()
                return

            assert mt == MessageType.BB84_CONFIRM
            qber = pl["qber"]
            log.log("qber_measured", qber=qber)

            # Remove sample bits from Bob's sifted key
            keep_mask = np.ones(len(bob_sifted), dtype=bool)
            keep_mask[sample_indices] = False
            bob_remaining = bob_sifted[keep_mask]

            # Error correction
            mt, pl = _recv()
            assert mt == MessageType.BB84_EC_PARITY
            alice_remaining_packed = base64.b64decode(pl["bits_b64"])
            alice_remaining = np.unpackbits(
                np.frombuffer(alice_remaining_packed, dtype=np.uint8)
            )[:int(pl["n"])].copy()

            corrected_bob, leaked = parity_error_correction(
                alice_remaining, bob_remaining, qber, rng
            )
            log.log("error_correction", leaked_bits=leaked)

            # Key confirmation
            keys_match = confirm_keys(alice_remaining, corrected_bob)
            _send(MessageType.BB84_CONFIRM, {"match": keys_match})
            if not keys_match:
                _send(MessageType.ABORT, {"reason": "Key confirmation failed"})
                log.log("aborted", reason="Key confirmation failed")
                log.flush()
                return

            # Privacy amplification
            mt, pl = _recv()
            assert mt == MessageType.BB84_PA_SEED
            pa_seed = base64.b64decode(pl["seed_b64"])

            try:
                qkd_key = privacy_amplification(
                    corrected_bob, self.cfg.FINAL_KEY_BITS, leaked, pa_seed
                )
            except InsufficientKeyError as exc:
                _send(MessageType.ABORT, {"reason": str(exc)})
                log.log("aborted", reason=str(exc))
                log.flush()
                return

            elapsed_bb84 = time.perf_counter() - t0
            log.log("bb84_completed", time_ms=elapsed_bb84 * 1000,
                     qkd_key_len=len(qkd_key))

        # ── PQC phase ─────────────────────────────────────────────────
        if self.mode in ("hybrid", "pqc"):
            t0 = time.perf_counter()
            kem = MLKEMKeyExchange(self.cfg.MLKEM_LEVEL)
            ek, dk = kem.generate_keypair()
            log.log("pqc_keygen", ek_len=len(ek))

            _send(MessageType.PQC_PUBLIC_KEY, {
                "ek_b64": base64.b64encode(ek).decode(),
                "level": self.cfg.MLKEM_LEVEL,
            })

            mt, pl = _recv()
            assert mt == MessageType.PQC_CIPHERTEXT
            ct = base64.b64decode(pl["ct_b64"])
            pq_secret = kem.decapsulate(dk, ct)
            log.log("pqc_decaps", ct_len=len(ct))
            log.log("pqc_completed", time_ms=(time.perf_counter() - t0) * 1000)

        # ── Classical phase ───────────────────────────────────────────
        if self.mode == "classical":
            kex = X25519KeyExchange()
            pub = kex.generate()
            _send(MessageType.PQC_PUBLIC_KEY, {
                "ek_b64": base64.b64encode(pub).decode(),
                "level": 0,
            })
            mt, pl = _recv()
            assert mt == MessageType.PQC_CIPHERTEXT
            peer_pub = base64.b64decode(pl["ct_b64"])
            classical_secret = kex.derive(peer_pub)

        # ── Derive hybrid key ─────────────────────────────────────────
        transcript_hash = hashlib.sha256(b"".join(transcript)).digest()
        combiner = HybridKeyCombiner(mode=self.mode, config=self.cfg)
        session_key = combiner.combine(
            qkd_key=qkd_key,
            pq_secret=pq_secret,
            classical_secret=classical_secret,
            transcript_hash=transcript_hash,
        )
        self.session_key_hash = hashlib.sha256(session_key).hexdigest()
        log.log("hybrid_key_derived", key_hash=self.session_key_hash)

        # ── Key confirmation via HMAC ─────────────────────────────────
        server_confirm = hmac.new(session_key, b"server-confirm" + transcript_hash, hashlib.sha256).hexdigest()
        _send(MessageType.KEY_CONFIRM, {"hmac": server_confirm})
        mt, pl = _recv()
        assert mt == MessageType.KEY_CONFIRM
        expected_client = hmac.new(session_key, b"client-confirm" + transcript_hash, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(pl["hmac"], expected_client):
            _send(MessageType.ABORT, {"reason": "Key confirmation HMAC mismatch"})
            log.log("aborted", reason="HMAC mismatch")
            log.flush()
            return

        log.log("key_confirmed")
        log.flush()
        print("[Server] ✅ Hybrid key established — secure chat ready.")

        # ── Encrypted chat ────────────────────────────────────────────
        channel = SecureChannel(session_key, "server")
        self._chat_loop(conn, channel, log)

    def _chat_loop(self, conn: socket.socket, channel: SecureChannel, log: EventLog) -> None:
        """Interactive encrypted chat (server side)."""
        stop = threading.Event()

        def _recv_loop() -> None:
            while not stop.is_set():
                try:
                    mt, pl, _ = recv_msg(conn)
                except (ConnectionError, OSError):
                    break
                if mt == MessageType.BYE:
                    print("\n[Server] Client disconnected.")
                    stop.set()
                    break
                if mt == MessageType.CHAT:
                    ct = base64.b64decode(pl["data"])
                    pt = channel.decrypt(ct)
                    print(f"\n[Alice] {pt.decode()}")
                    log.log("chat_received", size=len(pt))

        t = threading.Thread(target=_recv_loop, daemon=True)
        t.start()

        try:
            while not stop.is_set():
                try:
                    msg = input("[Bob] > ")
                except EOFError:
                    break
                if not msg:
                    continue
                if msg.strip() == "/quit":
                    send_msg(conn, MessageType.BYE, {})
                    break
                ct = channel.encrypt(msg.encode())
                send_msg(conn, MessageType.CHAT, {"data": base64.b64encode(ct).decode()})
                log.log("chat_sent", size=len(msg))
        except (ConnectionError, OSError):
            pass
        finally:
            stop.set()
            log.flush()


def main() -> None:
    """CLI entry point for the server."""
    parser = argparse.ArgumentParser(description="Hybrid QKD-PQC Server (Bob)")
    parser.add_argument("--mode", choices=["hybrid", "pqc", "qkd", "classical"],
                        default="hybrid")
    parser.add_argument("--eve-rate", type=float, default=0.0)
    parser.add_argument("--noise", type=float, default=0.0)
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--qubits", type=int, default=4096)
    args = parser.parse_args()

    cfg = Config()
    cfg.PORT = args.port
    cfg.N_QUBITS = args.qubits
    server = HybridServer(
        mode=args.mode, eve_rate=args.eve_rate, noise=args.noise,
        config=cfg,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down.")
        server.stop()


if __name__ == "__main__":
    main()
