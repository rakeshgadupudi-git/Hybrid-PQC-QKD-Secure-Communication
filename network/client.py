"""Alice (client) for the hybrid QKD-PQC secure communication protocol.

Connects to Bob (server), performs the hybrid handshake, derives a
session key, then enters an encrypted chat loop.

CLI usage::

    python -m network.client --mode hybrid
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
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

from bb84.postprocessing import (
    InsufficientKeyError,
    confirm_keys,
    estimate_qber,
    parity_error_correction,
    privacy_amplification,
    sift_keys,
)
from bb84.simulator import BB84Alice, QubitBatch
from classical.ecdh import X25519KeyExchange
from config import Config
from hybrid.combiner import HybridKeyCombiner
from network.event_log import EventLog
from network.protocol import MessageType, ProtocolError, recv_msg, send_msg
from network.secure_channel import SecureChannel
from pqc.mlkem import MLKEMKeyExchange

console = Console()


class HybridClient:
    """Alice's side of the hybrid handshake protocol.

    Args:
        mode: Handshake mode.
        config: Project configuration.
    """

    def __init__(
        self,
        mode: str = "hybrid",
        config: Config | None = None,
        n_qubits: int | None = None,
    ) -> None:
        self.mode = mode
        self.cfg = config or Config()
        if n_qubits is not None:
            self.cfg.N_QUBITS = n_qubits
        # Exposed for testing
        self.session_key_hash: str | None = None
        self.aborted: bool = False
        self.abort_reason: str | None = None

    def connect_and_run(self) -> None:
        """Connect to the server and run the full handshake + chat."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.cfg.HOST, self.cfg.PORT))
        try:
            self._run(sock)
        finally:
            sock.close()

    def _run(self, conn: socket.socket) -> None:
        """Execute the handshake protocol and chat."""
        log = EventLog("client", self.cfg)
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
        log.log("connected", host=self.cfg.HOST, port=self.cfg.PORT)
        mt, pl = _recv()  # server HELLO
        assert mt == MessageType.HELLO
        server_mode = pl.get("mode", self.mode)
        _send(MessageType.HELLO, {"mode": self.mode, "role": "client"})
        console.print(Panel(f"Connected to server — mode: [bold]{server_mode}[/bold]",
                            title="🔗 Handshake", border_style="cyan"))

        qkd_key: bytes | None = None
        pq_secret: bytes | None = None
        classical_secret: bytes | None = None

        # ── BB84 phase ────────────────────────────────────────────────
        if self.mode in ("hybrid", "qkd"):
            with Progress(console=console) as progress:
                task = progress.add_task("[cyan]BB84 handshake…", total=7)
                t0 = time.perf_counter()
                log.log("bb84_started", n_qubits=self.cfg.N_QUBITS)

                # Alice prepares qubits
                alice = BB84Alice(rng=rng)
                batch = alice.prepare(self.cfg.N_QUBITS)
                progress.advance(task)

                # Send qubits to Bob
                _send(MessageType.BB84_QUBITS, batch.to_wire())
                progress.advance(task)

                # Exchange bases
                mt, pl = _recv()
                assert mt == MessageType.BB84_BASES
                bob_bases = np.unpackbits(
                    np.frombuffer(base64.b64decode(pl["bases_b64"]), dtype=np.uint8)
                )[:int(pl["n"])].copy()
                _send(MessageType.BB84_BASES, {
                    "bases_b64": base64.b64encode(np.packbits(alice.bases).tobytes()).decode(),
                    "n": int(len(alice.bases)),
                })
                progress.advance(task)

                # Receive sifting result
                mt, pl = _recv()
                assert mt == MessageType.BB84_BASES_MATCH
                match_bits = np.unpackbits(
                    np.frombuffer(base64.b64decode(pl["kept_b64"]), dtype=np.uint8)
                )[:int(pl["n"])].copy()
                kept = np.nonzero(match_bits)[0]
                alice_sifted = alice.bits[kept]

                # QBER estimation
                sample_size = max(1, int(len(alice_sifted) * self.cfg.SAMPLE_FRACTION))
                sample_indices = rng.choice(len(alice_sifted), size=sample_size, replace=False)
                sample_indices.sort()
                _send(MessageType.BB84_SAMPLE, {"indices": sample_indices.tolist()})

                mt, pl = _recv()
                assert mt == MessageType.BB84_SAMPLE_REPLY
                bob_sample = np.array(pl["bits"], dtype=np.uint8)
                alice_sample = alice_sifted[sample_indices]
                errors = int(np.sum(alice_sample != bob_sample))
                qber = errors / sample_size
                progress.advance(task)

                log.log("qber_measured", qber=qber)

                if qber > self.cfg.QBER_THRESHOLD:
                    _send(MessageType.ABORT, {"reason": f"QBER {qber:.4f} > {self.cfg.QBER_THRESHOLD}"})
                    self.aborted = True
                    self.abort_reason = f"QBER {qber:.4f} exceeds threshold"
                    console.print(f"[bold red]❌ ABORT:[/bold red] QBER = {qber:.4f} (threshold {self.cfg.QBER_THRESHOLD})")
                    log.log("aborted", reason=self.abort_reason)
                    log.flush()
                    return

                console.print(f"[green]✓ QBER = {qber:.4f}[/green] (threshold {self.cfg.QBER_THRESHOLD})")
                _send(MessageType.BB84_CONFIRM, {"qber": qber})

                # Remove sample bits
                keep_mask = np.ones(len(alice_sifted), dtype=bool)
                keep_mask[sample_indices] = False
                alice_remaining = alice_sifted[keep_mask]

                # Error correction — send Alice's bits for parity checking
                _send(MessageType.BB84_EC_PARITY, {
                    "bits_b64": base64.b64encode(np.packbits(alice_remaining).tobytes()).decode(),
                    "n": int(len(alice_remaining)),
                })
                progress.advance(task)

                # Key confirmation
                mt, pl = _recv()
                assert mt == MessageType.BB84_CONFIRM
                if not pl.get("match", False):
                    self.aborted = True
                    self.abort_reason = "Key confirmation failed"
                    console.print("[bold red]❌ Key confirmation failed[/bold red]")
                    log.log("aborted", reason="Key confirmation failed")
                    log.flush()
                    return

                # Privacy amplification
                pa_seed = os.urandom(32)
                _send(MessageType.BB84_PA_SEED, {
                    "seed_b64": base64.b64encode(pa_seed).decode(),
                })

                # Alice also needs error correction result to match
                # In this simplified protocol, Alice uses her own bits
                # (the reference) since error correction makes Bob match Alice.
                leaked_bits = 0  # Alice doesn't know leaked count exactly, use 0 + margin handles it
                # We estimate leaked bits from QBER
                if qber > 0:
                    block_size = max(2, min(len(alice_remaining), int(0.73 / qber)))
                else:
                    block_size = 16
                n_blocks = (len(alice_remaining) + block_size - 1) // block_size
                leaked_bits = n_blocks * 10  # conservative estimate

                try:
                    qkd_key = privacy_amplification(
                        alice_remaining, self.cfg.FINAL_KEY_BITS, leaked_bits, pa_seed
                    )
                except InsufficientKeyError as exc:
                    self.aborted = True
                    self.abort_reason = str(exc)
                    console.print(f"[bold red]❌ {exc}[/bold red]")
                    log.log("aborted", reason=str(exc))
                    log.flush()
                    return

                progress.advance(task)
                elapsed = time.perf_counter() - t0
                log.log("bb84_completed", time_ms=elapsed * 1000, qkd_key_len=len(qkd_key))
                progress.advance(task)

        # ── PQC phase ─────────────────────────────────────────────────
        if self.mode in ("hybrid", "pqc"):
            mt, pl = _recv()
            assert mt == MessageType.PQC_PUBLIC_KEY
            ek = base64.b64decode(pl["ek_b64"])
            level = pl.get("level", self.cfg.MLKEM_LEVEL)
            log.log("pqc_keygen", ek_len=len(ek))

            kem = MLKEMKeyExchange(level=level)
            pq_secret, ct = kem.encapsulate(ek)
            log.log("pqc_encaps", ct_len=len(ct))
            _send(MessageType.PQC_CIPHERTEXT, {
                "ct_b64": base64.b64encode(ct).decode(),
            })
            console.print(f"[green]✓ ML-KEM-{level} encapsulation complete[/green]")

        # ── Classical phase ───────────────────────────────────────────
        if self.mode == "classical":
            mt, pl = _recv()
            assert mt == MessageType.PQC_PUBLIC_KEY
            peer_pub = base64.b64decode(pl["ek_b64"])
            kex = X25519KeyExchange()
            pub = kex.generate()
            _send(MessageType.PQC_CIPHERTEXT, {
                "ct_b64": base64.b64encode(pub).decode(),
            })
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
        mt, pl = _recv()
        assert mt == MessageType.KEY_CONFIRM
        expected_server = hmac.new(session_key, b"server-confirm" + transcript_hash, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(pl["hmac"], expected_server):
            self.aborted = True
            self.abort_reason = "Server HMAC mismatch"
            console.print("[bold red]❌ Key confirmation HMAC mismatch[/bold red]")
            log.flush()
            return

        client_confirm = hmac.new(session_key, b"client-confirm" + transcript_hash, hashlib.sha256).hexdigest()
        _send(MessageType.KEY_CONFIRM, {"hmac": client_confirm})

        log.log("key_confirmed")
        log.flush()
        console.print(Panel("✅ Hybrid key established — secure chat ready.",
                            title="🔐 Session Key", border_style="green"))

        # ── Encrypted chat ────────────────────────────────────────────
        channel = SecureChannel(session_key, "client")
        self._chat_loop(conn, channel, log)

    def _chat_loop(self, conn: socket.socket, channel: SecureChannel, log: EventLog) -> None:
        """Interactive encrypted chat (client side)."""
        stop = threading.Event()

        def _recv_loop() -> None:
            while not stop.is_set():
                try:
                    mt, pl, _ = recv_msg(conn)
                except (ConnectionError, OSError):
                    break
                if mt == MessageType.BYE:
                    console.print("\n[yellow]Server disconnected.[/yellow]")
                    stop.set()
                    break
                if mt == MessageType.CHAT:
                    ct = base64.b64decode(pl["data"])
                    pt = channel.decrypt(ct)
                    console.print(f"\n[bold blue][Bob][/bold blue] {pt.decode()}")
                    log.log("chat_received", size=len(pt))

        t = threading.Thread(target=_recv_loop, daemon=True)
        t.start()

        try:
            while not stop.is_set():
                try:
                    msg = input("[Alice] > ")
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
    """CLI entry point for the client."""
    parser = argparse.ArgumentParser(description="Hybrid QKD-PQC Client (Alice)")
    parser.add_argument("--mode", choices=["hybrid", "pqc", "qkd", "classical"],
                        default="hybrid")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--qubits", type=int, default=4096)
    args = parser.parse_args()

    cfg = Config()
    cfg.PORT = args.port
    cfg.N_QUBITS = args.qubits
    client = HybridClient(mode=args.mode, config=cfg)
    try:
        client.connect_and_run()
    except ConnectionRefusedError:
        console.print("[bold red]Cannot connect to server. Is it running?[/bold red]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Disconnected.[/yellow]")


if __name__ == "__main__":
    main()
