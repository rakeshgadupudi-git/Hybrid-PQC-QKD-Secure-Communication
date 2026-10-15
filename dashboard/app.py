"""Streamlit dashboard for the Hybrid QKD-PQC project.

Multi-page layout with Overview, BB84 Lab, Hybrid Handshake,
Benchmarks, and Demo Guide pages.

Run with::

    streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── Project root setup ────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bb84.session import BB84Result, qber_sweep, run_bb84_local
from config import Config

_CFG = Config()

# ── Page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hybrid QKD-PQC Dashboard",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Minimal dark-friendly CSS ─────────────────────────────────────────
st.markdown("""
<style>
    .footer { position: fixed; bottom: 0; left: 0; width: 100%;
              background: rgba(30,30,30,0.9); color: #aaa;
              text-align: center; padding: 6px; font-size: 0.75rem; z-index: 999; }
</style>
""", unsafe_allow_html=True)

_HONEST_LIMITS = (
    "⚠️ **Honest limitations:** BB84 is a software simulation, not real quantum "
    "hardware. `kyber-py` is a pure-Python educational implementation — not "
    "constant-time and **not for production**."
)

# ── Sidebar navigation ───────────────────────────────────────────────
page = st.sidebar.radio(
    "📂 Navigate",
    ["🏠 Overview", "🔬 BB84 Lab", "🤝 Hybrid Handshake",
     "📊 Benchmarks", "📖 Demo Guide"],
)


def _footer() -> None:
    st.markdown("---")
    st.caption(_HONEST_LIMITS)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Page 1: Overview
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if page == "🏠 Overview":
    st.title("🔐 Hybrid Quantum-Safe Secure Communication")
    st.subheader("Combining Post-Quantum Cryptography (ML-KEM) and Quantum Key Distribution (BB84)")

    st.markdown("""
    ### The Problem
    Quantum computers threaten today's public-key cryptography. A sufficiently
    powerful quantum computer running **Shor's algorithm** could break RSA and
    Elliptic-Curve Diffie-Hellman in polynomial time.

    ### Our Hybrid Solution
    We combine **two independent** quantum-resistant key-agreement mechanisms:

    1. **QKD (BB84 protocol)** — establishes a key whose security relies on the
       laws of quantum physics. Any eavesdropper introduces detectable errors.
    2. **PQC (ML-KEM-768 / FIPS 203)** — a lattice-based key encapsulation
       mechanism believed to be secure against quantum computers.

    Both keys are fused via **HKDF-SHA256** into one **hybrid session key**.
    The resulting channel is secure if **either** mechanism holds.
    """)

    # Architecture diagram using Plotly
    fig = go.Figure()
    # Boxes
    boxes = [
        (0.1, 0.8, "Alice\n(Client)"),
        (0.5, 0.8, "Quantum\nChannel\n(BB84)"),
        (0.9, 0.8, "Bob\n(Server)"),
        (0.3, 0.4, "ML-KEM-768\nEncapsulation"),
        (0.7, 0.4, "ML-KEM-768\nDecapsulation"),
        (0.5, 0.1, "HKDF-SHA256\n→ Hybrid Key\n→ AES-256-GCM"),
    ]
    for x, y, text in boxes:
        fig.add_shape(type="rect",
                      x0=x-0.12, y0=y-0.08, x1=x+0.12, y1=y+0.08,
                      fillcolor="rgba(99,110,250,0.2)",
                      line=dict(color="rgba(99,110,250,0.8)", width=2))
        fig.add_annotation(x=x, y=y, text=text, showarrow=False,
                          font=dict(size=11))

    # Arrows
    arrows = [
        (0.22, 0.8, 0.38, 0.8),  # Alice → Channel
        (0.62, 0.8, 0.78, 0.8),  # Channel → Bob
        (0.15, 0.72, 0.25, 0.48),  # Alice → ML-KEM enc
        (0.85, 0.72, 0.75, 0.48),  # Bob → ML-KEM dec
        (0.42, 0.4, 0.58, 0.4),   # enc → dec
        (0.5, 0.72, 0.5, 0.19),   # QKD key down
    ]
    for x0, y0, x1, y1 in arrows:
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0,
                          xref="x", yref="y", axref="x", ayref="y",
                          showarrow=True,
                          arrowhead=3, arrowsize=1.5,
                          arrowcolor="rgba(99,110,250,0.6)")

    fig.update_layout(
        xaxis=dict(range=[0, 1], visible=False),
        yaxis=dict(range=[0, 1], visible=False),
        height=450, margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.info(_HONEST_LIMITS)
    _footer()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Page 2: BB84 Lab
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "🔬 BB84 Lab":
    st.title("🔬 BB84 Quantum Key Distribution Lab")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        n_qubits = st.slider("Number of qubits", 256, 20000, 4096, step=256)
    with col2:
        eve_rate = st.slider("Eve intercept rate", 0.0, 1.0, 0.0, step=0.01)
    with col3:
        noise = st.slider("Channel noise", 0.0, 0.10, 0.0, step=0.005)
    with col4:
        seed_input = st.number_input("Seed (0 = random)", min_value=0, value=0, step=1)

    seed = int(seed_input) if seed_input > 0 else None

    if st.button("🚀 Run BB84", type="primary"):
        with st.spinner("Running BB84 protocol…"):
            result = run_bb84_local(n_qubits=n_qubits, eve_rate=eve_rate,
                                     noise=noise, seed=seed)

        # Metrics
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Sifted bits", result.sifted_len)
        c2.metric("QBER", f"{result.qber:.4f}")
        c3.metric("Status", "✅ Accepted" if result.accepted else "❌ Aborted")
        c4.metric("Final key (bytes)", len(result.final_key) if result.final_key else 0)
        c5.metric("Eve intercepted", result.eve_intercepted)

        if result.aborted_reason:
            st.error(f"**Aborted:** {result.aborted_reason}")

        # Key-bit funnel chart
        after_sample = result.sifted_len - result.sample_len
        after_ec = after_sample  # same length, just corrected
        final_bits = len(result.final_key) * 8 if result.final_key else 0
        funnel_data = {
            "Stage": ["Raw qubits", "Sifted", "After sampling", "After EC", "Final key"],
            "Bits": [n_qubits, result.sifted_len, after_sample, after_ec, final_bits],
        }
        fig_funnel = go.Figure(go.Bar(
            x=funnel_data["Stage"], y=funnel_data["Bits"],
            marker_color=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"],
        ))
        fig_funnel.update_layout(title="Key-Bit Funnel", yaxis_title="Bits",
                                  height=350)
        st.plotly_chart(fig_funnel, use_container_width=True)

    # QBER sweep chart
    st.subheader("QBER vs Eve Intercept Rate")

    @st.cache_data(show_spinner="Computing QBER sweep…")
    def _cached_sweep(n: int, trials: int, noise_val: float) -> pd.DataFrame:
        rates = np.linspace(0, 1, 21)
        return qber_sweep(rates, n_qubits=n, trials=trials, noise=noise_val)

    sweep_df = _cached_sweep(min(n_qubits, 4096), 3, noise)
    fig_sweep = go.Figure()
    fig_sweep.add_trace(go.Scatter(
        x=sweep_df["rate"], y=sweep_df["qber_mean"],
        mode="lines+markers", name="Measured QBER",
        error_y=dict(type="data", array=sweep_df["qber_std"].tolist(), visible=True),
    ))
    fig_sweep.add_trace(go.Scatter(
        x=[0, 1], y=[0, 0.25],
        mode="lines", name="Theoretical (0.25 × rate)",
        line=dict(dash="dash", color="gray"),
    ))
    fig_sweep.add_hline(y=0.11, line_dash="dot", line_color="red",
                         annotation_text="11% threshold")
    fig_sweep.update_layout(
        xaxis_title="Eve Intercept Rate",
        yaxis_title="QBER",
        height=400,
    )
    st.plotly_chart(fig_sweep, use_container_width=True)
    _footer()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Page 3: Hybrid Handshake
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "🤝 Hybrid Handshake":
    st.title("🤝 Hybrid Handshake Viewer")
    st.markdown("Reads the newest session log files from `logs/`.")

    log_dir = _CFG.LOG_DIR
    if log_dir.exists():
        logs = sorted(log_dir.glob("session_*.jsonl"), reverse=True)
    else:
        logs = []

    if not logs:
        st.warning("No log files found. Run a server–client demo first.")
    else:
        chosen = st.selectbox("Select log file", logs,
                               format_func=lambda p: p.name)
        if chosen:
            from network.event_log import EventLog
            entries = EventLog.read_log(chosen)
            if entries:
                df = pd.DataFrame(entries)
                df["ts_human"] = pd.to_datetime(df["ts"], unit="s").dt.strftime("%H:%M:%S.%f")

                # Step table
                st.subheader("Event Timeline")
                display_df = df[["ts_human", "role", "event"]].copy()
                details_col = []
                for _, row in df.iterrows():
                    d = row.get("details", {})
                    if isinstance(d, dict):
                        parts = [f"{k}={v}" for k, v in d.items()]
                        details_col.append(", ".join(parts[:5]))
                    else:
                        details_col.append(str(d))
                display_df["details"] = details_col
                st.dataframe(display_df, use_container_width=True)

                # Check if aborted
                aborted = any(e.get("event") == "aborted" for e in entries)
                if aborted:
                    st.error("❌ Session was **aborted**.")
                else:
                    st.success("✅ Session completed successfully.")

                # Timeline chart
                if len(entries) > 1:
                    ts0 = entries[0]["ts"]
                    times = [(e["ts"] - ts0) * 1000 for e in entries]
                    events = [e["event"] for e in entries]
                    fig_tl = go.Figure(go.Scatter(
                        x=times, y=events, mode="markers+lines",
                        marker=dict(size=10),
                    ))
                    fig_tl.update_layout(
                        title="Handshake Timeline",
                        xaxis_title="Time (ms from start)",
                        yaxis_title="Event",
                        height=400,
                    )
                    st.plotly_chart(fig_tl, use_container_width=True)
    _footer()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Page 4: Benchmarks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "📊 Benchmarks":
    st.title("📊 Benchmark Results")

    bench_file = _CFG.RESULTS_DIR / "benchmarks.json"

    if st.button("🔄 Run benchmarks now"):
        with st.spinner("Running benchmarks (this may take a minute)…"):
            subprocess.run(
                [sys.executable, "-m", "benchmarks.run_benchmarks", "--repeats", "10"],
                cwd=str(_ROOT),
            )
        st.rerun()

    if bench_file.exists():
        with bench_file.open() as f:
            data = json.load(f)

        # Key sizes chart
        st.subheader("Key & Ciphertext Sizes")
        labels = ["X25519", "RSA-2048", "ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"]
        key_sizes = [
            data["x25519"]["key_size"],
            data["rsa2048"]["key_size"],
            data["mlkem512"]["ek_size"],
            data["mlkem768"]["ek_size"],
            data["mlkem1024"]["ek_size"],
        ]
        ct_sizes = [
            data["x25519"]["ciphertext_size"],
            data["rsa2048"]["ciphertext_size"],
            data["mlkem512"]["ct_size"],
            data["mlkem768"]["ct_size"],
            data["mlkem1024"]["ct_size"],
        ]
        fig_sizes = go.Figure()
        fig_sizes.add_trace(go.Bar(name="Public Key", x=labels, y=key_sizes))
        fig_sizes.add_trace(go.Bar(name="Ciphertext", x=labels, y=ct_sizes))
        fig_sizes.update_layout(barmode="group", yaxis_title="Bytes", height=400)
        st.plotly_chart(fig_sizes, use_container_width=True)

        # Operation times
        st.subheader("ML-KEM Operation Times")
        levels = [512, 768, 1024]
        ops = ["keygen", "encaps", "decaps"]
        fig_ops = go.Figure()
        for op in ops:
            means = [data[f"mlkem{lv}"][op]["mean"] * 1000 for lv in levels]
            fig_ops.add_trace(go.Bar(name=op, x=[f"ML-KEM-{lv}" for lv in levels], y=means))
        fig_ops.update_layout(barmode="group", yaxis_title="Time (ms)", height=400)
        st.plotly_chart(fig_ops, use_container_width=True)

        # BB84 runtime
        st.subheader("BB84 Runtime vs Qubits")
        bb84 = data.get("bb84_runtime", {})
        if bb84:
            ns = sorted(bb84.keys(), key=int)
            means = [bb84[n]["mean"] * 1000 for n in ns]
            fig_bb84 = go.Figure(go.Scatter(
                x=[int(n) for n in ns], y=means,
                mode="lines+markers",
            ))
            fig_bb84.update_layout(
                xaxis_title="Number of Qubits",
                yaxis_title="Runtime (ms)",
                height=400,
            )
            st.plotly_chart(fig_bb84, use_container_width=True)
    else:
        st.info("No benchmark results found. Click the button above to run benchmarks.")
    _footer()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Page 5: Demo Guide
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "📖 Demo Guide":
    st.title("📖 Demo Guide")

    st.markdown("""
    ### Prerequisites
    ```powershell
    cd hybrid-qkd-pqc
    .venv\\Scripts\\Activate.ps1
    ```

    ### 1. Run the secure chat (no eavesdropper)
    Open **two** PowerShell windows:

    **Window 1 (Server / Bob):**
    ```powershell
    python -m network.server --mode hybrid
    ```

    **Window 2 (Client / Alice):**
    ```powershell
    python -m network.client --mode hybrid
    ```

    Both sides will perform the BB84 + ML-KEM handshake, derive the
    hybrid session key, and enter an encrypted chat. Type messages and
    press Enter. Type `/quit` to disconnect.

    ### 2. Run with Eve (eavesdropper attack)
    **Window 1 (Server with Eve):**
    ```powershell
    python -m network.server --mode hybrid --eve-rate 1.0
    ```

    **Window 2 (Client):**
    ```powershell
    python -m network.client --mode hybrid
    ```

    The QBER will be ~25% and **both sides will abort** the connection,
    demonstrating that the BB84 protocol detects eavesdropping.

    ### 3. Using the demo scripts
    ```powershell
    # Normal run
    .\\scripts\\run_demo.ps1

    # With Eve
    .\\scripts\\run_demo.ps1 -EveRate 1.0

    # PQC-only mode
    .\\scripts\\run_demo.ps1 -Mode pqc
    ```

    ### 4. Run the benchmarks
    ```powershell
    python -m benchmarks.run_benchmarks --repeats 30
    ```

    ### 5. Run the tests
    ```powershell
    python -m pytest tests/ -v
    ```

    ### 6. Launch this dashboard
    ```powershell
    streamlit run dashboard/app.py
    ```
    """)
    _footer()
