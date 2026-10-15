export default function About() {
  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Title */}
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2 text-text">
          <span>ℹ️</span> About the Hybrid QKD + PQC Cryptographic Architecture
        </h2>
        <p className="text-sm text-text-dim mt-1">
          7th Semester Capstone Project in Quantum-Safe Cryptography (QSC) — Indian Institute of Information Technology Dharwad (IIIT Dharwad).
        </p>
      </div>

      {/* Architecture Summary */}
      <div className="card space-y-4">
        <h3 className="text-base font-bold text-text flex items-center gap-2">
          <span>🛡️</span> Project Vision & Overview
        </h3>
        <p className="text-xs sm:text-sm text-text-dim leading-relaxed">
          The emergence of Cryptanalytically Relevant Quantum Computers (CRQCs) poses an existential threat to current public-key cryptography (RSA, ECDH, ECDSA) due to Shor's algorithm. To safeguard sensitive long-term communications against the urgent <strong>Harvest Now, Decrypt Later (HNDL)</strong> attack model, this project implements a production-grade <strong>Hybrid Quantum-Safe Handshake</strong>.
        </p>
        <p className="text-xs sm:text-sm text-text-dim leading-relaxed">
          By combining the physical guarantees of <strong>Quantum Key Distribution (BB84)</strong> with the algorithmic hardness of <strong>Post-Quantum Cryptography (ML-KEM / FIPS 203)</strong> using an <strong>HKDF-SHA256</strong> combiner, our system provides rigorous defense-in-depth: total confidentiality is preserved even if one of the underlying cryptographic mechanisms is completely broken in the future.
        </p>
      </div>

      {/* Protocol Diagram / Flow */}
      <div className="card space-y-4">
        <h3 className="text-base font-bold text-text flex items-center gap-2">
          <span>🔄</span> Multi-Stage Handshake Architecture
        </h3>
        <p className="text-xs text-text-dim">
          The 6 stages and 14 verifiable protocol steps executed during every session establishment:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
          <div className="p-3 bg-surface-2 rounded-xl border border-border space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-qkd">STAGE 1: BB84 QKD</span>
              <span className="badge bg-qkd/20 text-qkd text-[10px]">Steps 1–5</span>
            </div>
            <p className="text-xs text-text-dim">
              Alice prepares photons in random bases ({'{0,1}'} in {'{+,×}'}); Bob measures; bases are sifted over an authenticated channel (~50% retention).
            </p>
          </div>

          <div className="p-3 bg-surface-2 rounded-xl border border-border space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-rose-400">STAGE 2: EVE CHECK & CLEANUP</span>
              <span className="badge bg-rose-500/20 text-rose-400 text-[10px]">Steps 6–8</span>
            </div>
            <p className="text-xs text-text-dim">
              25% sample bit comparison computes QBER. If &gt;11%, session aborts. Cascade fixes residual noise; Toeplitz universal hashing distills 256-bit key.
            </p>
          </div>

          <div className="p-3 bg-surface-2 rounded-xl border border-border space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-pqc">STAGE 3: ML-KEM PQC</span>
              <span className="badge bg-pqc/20 text-pqc text-[10px]">Steps 9–11</span>
            </div>
            <p className="text-xs text-text-dim">
              Bob generates Module-LWE public/private keypair (FIPS 203). Alice encapsulates a 32-byte shared secret into ciphertext; Bob decapsulates.
            </p>
          </div>

          <div className="p-3 bg-surface-2 rounded-xl border border-border space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-hybrid">STAGE 4: HKDF COMBINER</span>
              <span className="badge bg-hybrid/20 text-hybrid text-[10px]">Step 12</span>
            </div>
            <p className="text-xs text-text-dim">
              HKDF-Extract & Expand mixes length-prefixed QKD key, PQC secret, and transcript hash salt into a uniform 256-bit symmetric session key.
            </p>
          </div>

          <div className="p-3 bg-surface-2 rounded-xl border border-border space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-alice">STAGE 5: KEY CONFIRMATION</span>
              <span className="badge bg-alice/20 text-alice text-[10px]">Step 13</span>
            </div>
            <p className="text-xs text-text-dim">
              Mutual exchange of HMAC-SHA256 tags computed over role tags and handshake transcript verifies that both peers hold identical keys.
            </p>
          </div>

          <div className="p-3 bg-surface-2 rounded-xl border border-border space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-bob">STAGE 6: SECURE CHAT</span>
              <span className="badge bg-bob/20 text-bob text-[10px]">Step 14</span>
            </div>
            <p className="text-xs text-text-dim">
              AES-256-GCM AEAD encryption protects application payloads. 96-bit nonces with 64-bit sequence counters prevent replay and reordering.
            </p>
          </div>
        </div>
      </div>

      {/* Course Objective Mapping */}
      <div className="card space-y-4">
        <h3 className="text-base font-bold text-text flex items-center gap-2">
          <span>🎓</span> Academic Course Objective Mapping (QSC Curriculum)
        </h3>

        <div className="space-y-3 text-xs sm:text-sm">
          <div className="p-3 bg-surface-2 rounded-lg border border-border">
            <div className="font-bold text-text mb-1">
              Objective 1: Quantum Key Distribution (QKD) & Simulation
            </div>
            <p className="text-text-dim text-xs">
              Demonstrated through a full discrete-event BB84 simulator with conjugate polarization bases, quantum measurement collapse, intercept-resend eavesdropping, classical sifting, Cascade error correction, and Toeplitz-matrix privacy amplification.
            </p>
          </div>

          <div className="p-3 bg-surface-2 rounded-lg border border-border">
            <div className="font-bold text-text mb-1">
              Objective 2: Post-Quantum Cryptography (PQC) Standards
            </div>
            <p className="text-text-dim text-xs">
              Demonstrated through integration of NIST FIPS 203 (ML-KEM-512, ML-KEM-768, ML-KEM-1024) lattice-based cryptography, evaluating public key/ciphertext wire overhead versus classical ECDH.
            </p>
          </div>

          <div className="p-3 bg-surface-2 rounded-lg border border-border">
            <div className="font-bold text-text mb-1">
              Objective 3: Hybrid Cryptographic Combiner Architecture
            </div>
            <p className="text-text-dim text-xs">
              Demonstrated through an RFC 5869 / NIST SP 800-56C compliant HKDF engine that binds session transcripts and combines disparate entropy pools into a single uncompromised session key.
            </p>
          </div>

          <div className="p-3 bg-surface-2 rounded-lg border border-border">
            <div className="font-bold text-text mb-1">
              Objective 4: Threat Modeling, Active Attacks & Secure Channel Verification
            </div>
            <p className="text-text-dim text-xs">
              Demonstrated through an interactive Attack Lab executing photon interception attacks, ciphertext bit-flipping attacks, and message replay attacks, validated with automated self-tests and protection scorecards.
            </p>
          </div>
        </div>
      </div>

      {/* Honest Limitations */}
      <div className="card space-y-3 border-amber-500/40 bg-amber-500/5">
        <h3 className="text-base font-bold text-amber-400 flex items-center gap-2">
          <span>⚠️</span> Honest Engineering Limitations & Real-World Deployment Notes
        </h3>
        <ul className="list-disc pl-5 space-y-2 text-xs sm:text-sm text-text-dim">
          <li>
            <strong>Software Simulation of BB84:</strong> In this laboratory implementation, quantum states and photon transmissions are modeled computationally. Real-world BB84 requires attenuated pulsed laser diodes, polarization controllers, dark-fiber optical links, and single-photon avalanche photodiode (SPAD) detectors.
          </li>
          <li>
            <strong>Constant-Time Execution:</strong> The underlying <code className="font-mono text-pqc">kyber-py</code> library is an educational reference implementation and is not protected against physical side-channel timing attacks (such as cache-timing or power analysis). Production environments should use C/Rust vectorized implementations (e.g., liboqs).
          </li>
          <li>
            <strong>Classical Channel Authentication:</strong> Standard BB84 relies on an authenticated classical channel to prevent active man-in-the-middle attacks during basis sifting. In a real-world deployment, this is typically provisioned via pre-shared symmetric keys (Wegman-Carter MACs) or post-quantum digital signatures (ML-DSA / FIPS 204).
          </li>
        </ul>
      </div>
    </div>
  );
}
