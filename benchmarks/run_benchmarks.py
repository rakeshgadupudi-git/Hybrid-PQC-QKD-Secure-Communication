"""Benchmark suite for classical, PQC, and hybrid key exchange.

CLI usage::

    python -m benchmarks.run_benchmarks --repeats 30
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from rich.console import Console
from rich.table import Table

# Ensure project root is on sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bb84.session import run_bb84_local
from classical.ecdh import RSAKeyTransport, X25519KeyExchange
from config import Config
from pqc.mlkem import MLKEMKeyExchange

console = Console()


def _time_fn(fn, repeats: int) -> dict[str, float]:
    """Time a callable over *repeats* iterations.

    Returns:
        Dict with ``mean``, ``median``, ``std`` in seconds.
    """
    times: list[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    arr = np.array(times)
    return {"mean": float(arr.mean()), "median": float(np.median(arr)), "std": float(arr.std())}


def run_benchmarks(repeats: int = 30) -> dict[str, Any]:
    """Execute all benchmarks and return structured results.

    Args:
        repeats: Number of repetitions per measurement.

    Returns:
        Nested dict of all results.
    """
    results: dict[str, Any] = {}

    # ── X25519 ────────────────────────────────────────────────────────
    console.print("[bold cyan]Benchmarking X25519…[/bold cyan]")
    def x25519_exchange() -> None:
        a = X25519KeyExchange()
        b = X25519KeyExchange()
        pa = a.generate()
        pb = b.generate()
        a.derive(pb)
        b.derive(pa)

    results["x25519"] = _time_fn(x25519_exchange, repeats)
    results["x25519"]["key_size"] = 32
    results["x25519"]["ciphertext_size"] = 32  # public key

    # ── RSA-2048 ──────────────────────────────────────────────────────
    console.print("[bold cyan]Benchmarking RSA-2048…[/bold cyan]")
    def rsa_transport() -> None:
        r = RSAKeyTransport()
        pub = r.generate_keypair()
        secret = os.urandom(32)
        ct = r.encrypt(pub, secret)
        _ = r.decrypt(ct)

    results["rsa2048"] = _time_fn(rsa_transport, repeats)
    results["rsa2048"]["key_size"] = 294  # DER pub key approx
    results["rsa2048"]["ciphertext_size"] = 256

    # ── ML-KEM ────────────────────────────────────────────────────────
    for level in (512, 768, 1024):
        label = f"mlkem{level}"
        console.print(f"[bold cyan]Benchmarking ML-KEM-{level}…[/bold cyan]")
        kem = MLKEMKeyExchange(level=level)
        sizes = kem.sizes()

        results[label] = {}
        results[label]["keygen"] = _time_fn(lambda: kem.generate_keypair(), repeats)
        ek, dk = kem.generate_keypair()
        results[label]["encaps"] = _time_fn(lambda: kem.encapsulate(ek), repeats)
        _, ct = kem.encapsulate(ek)
        results[label]["decaps"] = _time_fn(lambda: kem.decapsulate(dk, ct), repeats)
        results[label]["ek_size"] = sizes.ek
        results[label]["dk_size"] = sizes.dk
        results[label]["ct_size"] = sizes.ct
        results[label]["ss_size"] = sizes.ss

    # ── BB84 runtime vs qubit count ───────────────────────────────────
    console.print("[bold cyan]Benchmarking BB84 runtime…[/bold cyan]")
    bb84_results: dict[str, dict[str, float]] = {}
    for n in (512, 1024, 2048, 4096, 8192):
        console.print(f"  n_qubits={n}")
        times: list[float] = []
        for trial in range(min(repeats, 10)):
            t0 = time.perf_counter()
            run_bb84_local(n_qubits=n, eve_rate=0.0, noise=0.0, seed=trial)
            times.append(time.perf_counter() - t0)
        arr = np.array(times)
        bb84_results[str(n)] = {
            "mean": float(arr.mean()),
            "median": float(np.median(arr)),
            "std": float(arr.std()),
        }
    results["bb84_runtime"] = bb84_results

    return results


def save_results(results: dict[str, Any], cfg: Config | None = None) -> None:
    """Save benchmark results to JSON, CSV, and PNG charts.

    Args:
        results: The results dict from :func:`run_benchmarks`.
        cfg: Optional configuration.
    """
    c = cfg or Config()
    out = c.RESULTS_DIR

    # JSON
    with (out / "benchmarks.json").open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # CSV
    import pandas as pd
    rows = []
    for key in ("x25519", "rsa2048"):
        rows.append({"algorithm": key, "operation": "exchange",
                      "mean_s": results[key]["mean"],
                      "median_s": results[key]["median"],
                      "std_s": results[key]["std"],
                      "key_size": results[key].get("key_size", ""),
                      "ct_size": results[key].get("ciphertext_size", "")})
    for level in (512, 768, 1024):
        label = f"mlkem{level}"
        for op in ("keygen", "encaps", "decaps"):
            rows.append({"algorithm": label, "operation": op,
                          "mean_s": results[label][op]["mean"],
                          "median_s": results[label][op]["median"],
                          "std_s": results[label][op]["std"],
                          "key_size": results[label].get("ek_size", ""),
                          "ct_size": results[label].get("ct_size", "")})
    df = pd.DataFrame(rows)
    df.to_csv(out / "benchmarks.csv", index=False)

    # Charts
    _plot_key_sizes(results, out)
    _plot_operation_times(results, out)
    _plot_bb84_runtime(results, out)
    console.print(f"[green]Results saved to {out}[/green]")


def _plot_key_sizes(results: dict[str, Any], out: Path) -> None:
    """Bar chart: key and ciphertext sizes."""
    labels = ["X25519", "RSA-2048", "ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"]
    key_sizes = [
        results["x25519"]["key_size"],
        results["rsa2048"]["key_size"],
        results["mlkem512"]["ek_size"],
        results["mlkem768"]["ek_size"],
        results["mlkem1024"]["ek_size"],
    ]
    ct_sizes = [
        results["x25519"]["ciphertext_size"],
        results["rsa2048"]["ciphertext_size"],
        results["mlkem512"]["ct_size"],
        results["mlkem768"]["ct_size"],
        results["mlkem1024"]["ct_size"],
    ]

    x = np.arange(len(labels))
    w = 0.35
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w / 2, key_sizes, w, label="Public key / EK")
    ax.bar(x + w / 2, ct_sizes, w, label="Ciphertext")
    ax.set_ylabel("Bytes")
    ax.set_title("Key & Ciphertext Sizes: Classical vs Post-Quantum")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "key_sizes.png", dpi=150)
    plt.close(fig)


def _plot_operation_times(results: dict[str, Any], out: Path) -> None:
    """Bar chart: operation times for ML-KEM levels."""
    levels = [512, 768, 1024]
    ops = ["keygen", "encaps", "decaps"]
    x = np.arange(len(levels))
    w = 0.25

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, op in enumerate(ops):
        means = [results[f"mlkem{lv}"][op]["mean"] * 1000 for lv in levels]
        ax.bar(x + i * w, means, w, label=op)
    ax.set_ylabel("Time (ms)")
    ax.set_title("ML-KEM Operation Times")
    ax.set_xticks(x + w)
    ax.set_xticklabels([f"ML-KEM-{lv}" for lv in levels])
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "operation_times.png", dpi=150)
    plt.close(fig)


def _plot_bb84_runtime(results: dict[str, Any], out: Path) -> None:
    """Line chart: BB84 runtime vs number of qubits."""
    bb84 = results["bb84_runtime"]
    ns = sorted(bb84.keys(), key=int)
    means = [bb84[n]["mean"] * 1000 for n in ns]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot([int(n) for n in ns], means, marker="o", linewidth=2)
    ax.set_xlabel("Number of qubits")
    ax.set_ylabel("Runtime (ms)")
    ax.set_title("BB84 Runtime vs Number of Qubits")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "bb84_runtime.png", dpi=150)
    plt.close(fig)


def _print_table(results: dict[str, Any]) -> None:
    """Pretty-print results with Rich."""
    table = Table(title="Benchmark Results")
    table.add_column("Algorithm", style="cyan")
    table.add_column("Operation", style="magenta")
    table.add_column("Mean (ms)", justify="right")
    table.add_column("Median (ms)", justify="right")
    table.add_column("Std (ms)", justify="right")

    for key in ("x25519", "rsa2048"):
        table.add_row(key, "exchange",
                       f"{results[key]['mean']*1000:.3f}",
                       f"{results[key]['median']*1000:.3f}",
                       f"{results[key]['std']*1000:.3f}")

    for level in (512, 768, 1024):
        label = f"mlkem{level}"
        for op in ("keygen", "encaps", "decaps"):
            table.add_row(label, op,
                           f"{results[label][op]['mean']*1000:.3f}",
                           f"{results[label][op]['median']*1000:.3f}",
                           f"{results[label][op]['std']*1000:.3f}")

    table.add_section()
    for n, data in sorted(results["bb84_runtime"].items(), key=lambda x: int(x[0])):
        table.add_row("bb84", f"n={n}",
                       f"{data['mean']*1000:.3f}",
                       f"{data['median']*1000:.3f}",
                       f"{data['std']*1000:.3f}")

    console.print(table)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run hybrid QKD-PQC benchmarks")
    parser.add_argument("--repeats", type=int, default=30)
    args = parser.parse_args()

    results = run_benchmarks(repeats=args.repeats)
    save_results(results)
    _print_table(results)


if __name__ == "__main__":
    main()
