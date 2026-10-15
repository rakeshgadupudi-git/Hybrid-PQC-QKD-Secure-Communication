import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { postAttackEve, postAttackTamper, postAttackReplay, postChatStart, fetchCompare } from '../api/client';
import QberGauge from '../components/QberGauge';

export default function AttackLab() {
  // Eve attack state
  const [eveRate, setEveRate] = useState(1.0);
  const [qubits, setQubits] = useState(4000);
  const [eveLoading, setEveLoading] = useState(false);
  const [eveResult, setEveResult] = useState(null);

  // Tamper attack state
  const [tamperMsg, setTamperMsg] = useState('Secret bank transfer: send $10,000 to Bob.');
  const [tamperLoading, setTamperLoading] = useState(false);
  const [tamperResult, setTamperResult] = useState(null);

  // Replay attack state
  const [replayMsg, setReplayMsg] = useState('Authorize payment #98234.');
  const [replayLoading, setReplayLoading] = useState(false);
  const [replayResult, setReplayResult] = useState(null);

  // Shared session ID for attacks
  const [sessionId, setSessionId] = useState(null);

  // Compare stats for "Why Quantum-Safe?" panel
  const [compareStats, setCompareStats] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);

  // Init session & fetch compare data
  useEffect(() => {
    async function init() {
      try {
        const sess = await postChatStart({ mode: 'hybrid', qubits: 2048 });
        if (sess.session_id) setSessionId(sess.session_id);
      } catch (err) {
        console.warn('Initial session creation:', err);
      }

      setCompareLoading(true);
      try {
        const stats = await fetchCompare();
        setCompareStats(stats);
      } catch (err) {
        console.warn('Failed to fetch compare data:', err);
      } finally {
        setCompareLoading(false);
      }
    }
    init();
  }, []);

  // Handler for Eve attack
  const handleEveAttack = async () => {
    setEveLoading(true);
    setEveResult(null);
    try {
      const res = await postAttackEve({ qubits, eve_rate: eveRate });
      setEveResult(res);
    } catch (err) {
      console.error('Eve attack failed:', err);
    } finally {
      setEveLoading(false);
    }
  };

  // Handler for Tamper attack
  const handleTamperAttack = async () => {
    setTamperLoading(true);
    setTamperResult(null);
    try {
      let sId = sessionId;
      if (!sId) {
        const sess = await postChatStart({ mode: 'hybrid', qubits: 2048 });
        sId = sess.session_id;
        setSessionId(sId);
      }
      const res = await postAttackTamper({
        session_id: sId,
        sender: 'alice',
        text: tamperMsg,
      });
      setTamperResult(res);
    } catch (err) {
      console.error('Tamper attack failed:', err);
    } finally {
      setTamperLoading(false);
    }
  };

  // Handler for Replay attack
  const handleReplayAttack = async () => {
    setReplayLoading(true);
    setReplayResult(null);
    try {
      let sId = sessionId;
      if (!sId) {
        const sess = await postChatStart({ mode: 'hybrid', qubits: 2048 });
        sId = sess.session_id;
        setSessionId(sId);
      }
      const res = await postAttackReplay({
        session_id: sId,
        sender: 'alice',
        text: replayMsg,
      });
      setReplayResult(res);
    } catch (err) {
      console.error('Replay attack failed:', err);
    } finally {
      setReplayLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2 text-text">
          <span>🧪</span> Cryptographic Attack Lab
        </h2>
        <p className="text-sm text-text-dim mt-1">
          Simulate real adversary capabilities against the quantum, key-agreement, and message layers to observe cryptographic defenses in action.
        </p>
      </div>

      {/* Grid of 3 Attack Demos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ATTACK 1: EVE INTERCEPT-RESEND */}
        <div className="card flex flex-col justify-between space-y-4 border-t-4 border-t-eve">
          <div>
            <div className="flex items-center justify-between">
              <span className="badge bg-eve/20 text-eve font-bold text-xs">
                ATTACK #1: QUANTUM LINK
              </span>
              <span className="text-xs font-mono text-text-dim">Layer 1 (BB84)</span>
            </div>

            <h3 className="text-base font-bold text-text mt-2">
              🕵️ Intercept-Resend Attack (Eve)
            </h3>
            <p className="text-xs text-text-dim mt-1">
              Eve taps the fiber and measures transmitted photons in random bases, re-preparing new photons to send to Bob.
            </p>

            <div className="space-y-3 mt-4 pt-3 border-t border-border">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-text-dim">Interception Rate:</span>
                  <span className="font-mono text-eve font-bold">{Math.round(eveRate * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="1.0"
                  step="0.05"
                  value={eveRate}
                  onChange={(e) => setEveRate(parseFloat(e.target.value))}
                  className="w-full accent-eve"
                />
              </div>

              <div>
                <label className="text-xs text-text-dim block mb-1">Qubits count:</label>
                <select
                  value={qubits}
                  onChange={(e) => setQubits(parseInt(e.target.value))}
                  className="input w-full text-xs"
                >
                  <option value={2048}>2,048 qubits</option>
                  <option value={4000}>4,000 qubits (Recommended)</option>
                  <option value={8192}>8,192 qubits</option>
                </select>
              </div>

              <button
                onClick={handleEveAttack}
                disabled={eveLoading}
                className="btn-danger w-full text-xs font-bold mt-2"
              >
                {eveLoading ? 'Simulating Interception...' : '🚀 Execute Eve Attack'}
              </button>
            </div>
          </div>

          {/* Results display */}
          <AnimatePresence>
            {eveResult && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-surface-2 rounded-lg border border-border space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs text-text-dim">Decision:</span>
                  <span
                    className={`badge font-bold text-xs ${
                      eveResult.decision === 'abort'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                        : 'bg-emerald-500/20 text-emerald-400'
                    }`}
                  >
                    {eveResult.decision === 'abort' ? '🚨 HANDSHAKE ABORTED' : '✅ ACCEPTED'}
                  </span>
                </div>

                <div className="space-y-1 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-text-dim">Measured QBER:</span>
                    <strong className="text-eve">{(eveResult.qber_with_eve * 100).toFixed(2)}%</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-dim">Baseline (0% Eve):</span>
                    <strong className="text-bob">{(eveResult.qber_baseline * 100).toFixed(2)}%</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-dim">Theory (0.25 × rate):</span>
                    <strong className="text-text">{(eveResult.theoretical * 100).toFixed(2)}%</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-dim">Abort Threshold:</span>
                    <strong className="text-amber-400">11.00%</strong>
                  </div>
                </div>

                <div className="p-2 bg-rose-500/10 rounded border border-rose-500/30 text-[11px] text-rose-300">
                  🛡️ <strong>What stopped it:</strong> No-cloning theorem. Measuring unknown quantum states irreversibly disturbs 25% of sifted bits. The QBER exceeded 11%, triggering automatic protocol termination.
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* ATTACK 2: TAMPER MESSAGE */}
        <div className="card flex flex-col justify-between space-y-4 border-t-4 border-t-amber-500">
          <div>
            <div className="flex items-center justify-between">
              <span className="badge bg-amber-500/20 text-amber-400 font-bold text-xs">
                ATTACK #2: WIRE INTEGRITY
              </span>
              <span className="text-xs font-mono text-text-dim">Layer 3 (AEAD)</span>
            </div>

            <h3 className="text-base font-bold text-text mt-2">
              ⚡ Ciphertext Tampering (Bit-Flip)
            </h3>
            <p className="text-xs text-text-dim mt-1">
              An active man-in-the-middle flips bits in the ciphertext during transit to alter transaction amounts or commands.
            </p>

            <div className="space-y-3 mt-4 pt-3 border-t border-border">
              <div>
                <label className="text-xs text-text-dim block mb-1">Message to Encrypt:</label>
                <input
                  type="text"
                  value={tamperMsg}
                  onChange={(e) => setTamperMsg(e.target.value)}
                  className="input w-full text-xs"
                />
              </div>

              <button
                onClick={handleTamperAttack}
                disabled={tamperLoading}
                className="btn-secondary w-full text-xs font-bold border-amber-500/50 hover:bg-amber-500/10 text-amber-400 mt-2"
              >
                {tamperLoading ? 'Tampering...' : '⚡ Encrypt, Flip Bit & Deliver'}
              </button>
            </div>
          </div>

          {/* Results display */}
          <AnimatePresence>
            {tamperResult && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-surface-2 rounded-lg border border-border space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="text-text-dim">Integrity Check:</span>
                  <span className="badge bg-rose-500/20 text-rose-400 font-bold">
                    REJECTED (AEAD TAG FAILED)
                  </span>
                </div>

                <div className="font-mono text-[11px] text-amber-400 bg-surface-3 p-2 rounded break-all">
                  Ciphertext: {tamperResult.ciphertext_hex_preview}
                </div>

                <div className="text-[11px] text-text-dim font-mono">
                  Error: {tamperResult.error || 'Authentication tag verification failed'}
                </div>

                <div className="p-2 bg-emerald-500/10 rounded border border-emerald-500/30 text-[11px] text-emerald-300">
                  🛡️ <strong>What stopped it:</strong> AES-256-GCM Galois Message Authentication Code (GMAC). Modifying even 1 bit corrupts the 128-bit MAC tag, causing immediate ciphertext rejection prior to plaintext release.
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* ATTACK 3: REPLAY ATTACK */}
        <div className="card flex flex-col justify-between space-y-4 border-t-4 border-t-alice">
          <div>
            <div className="flex items-center justify-between">
              <span className="badge bg-alice/20 text-alice font-bold text-xs">
                ATTACK #3: REPLAY ATTACK
              </span>
              <span className="text-xs font-mono text-text-dim">Layer 3 (Nonces)</span>
            </div>

            <h3 className="text-base font-bold text-text mt-2">
              🔄 Message Replay & Re-order
            </h3>
            <p className="text-xs text-text-dim mt-1">
              An attacker intercepts a legitimate encrypted message and transmits a duplicate copy later to repeat actions.
            </p>

            <div className="space-y-3 mt-4 pt-3 border-t border-border">
              <div>
                <label className="text-xs text-text-dim block mb-1">Target Message:</label>
                <input
                  type="text"
                  value={replayMsg}
                  onChange={(e) => setReplayMsg(e.target.value)}
                  className="input w-full text-xs"
                />
              </div>

              <button
                onClick={handleReplayAttack}
                disabled={replayLoading}
                className="btn-secondary w-full text-xs font-bold border-alice/50 hover:bg-alice/10 text-alice mt-2"
              >
                {replayLoading ? 'Replaying...' : '🔄 Send Valid Then Re-Send Duplicate'}
              </button>
            </div>
          </div>

          {/* Results display */}
          <AnimatePresence>
            {replayResult && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-surface-2 rounded-lg border border-border space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="text-text-dim">1st Delivery:</span>
                  <span className="badge bg-emerald-500/20 text-emerald-400 font-bold">
                    {replayResult.first_delivery}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-text-dim">2nd Delivery (Replay):</span>
                  <span className="badge bg-rose-500/20 text-rose-400 font-bold">
                    REJECTED BY COUNTER
                  </span>
                </div>

                <div className="text-[11px] text-text-dim font-mono">
                  Error: {replayResult.error || 'Counter mismatch: sequence number already observed'}
                </div>

                <div className="p-2 bg-emerald-500/10 rounded border border-emerald-500/30 text-[11px] text-emerald-300">
                  🛡️ <strong>What stopped it:</strong> Strictly monotonic 64-bit sequence counters embedded in the 96-bit AES-GCM nonce and authenticated as AAD. Replays fail the nonce freshness check.
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* WHY QUANTUM-SAFE PANEL */}
      <div className="card space-y-4 bg-gradient-to-br from-surface to-surface-2 border-alice/40">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-3">
          <div>
            <h3 className="text-lg font-bold flex items-center gap-2 text-text">
              <span>🛡️</span> Why Quantum-Safe? "Harvest Now, Decrypt Later"
            </h3>
            <p className="text-xs text-text-dim">
              The urgent real-world rationale for combining Post-Quantum Cryptography and Quantum Key Distribution.
            </p>
          </div>
          <span className="badge bg-pqc/20 text-pqc font-mono font-bold">
            Defense-in-Depth
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-text-dim leading-relaxed">
          <div className="space-y-3">
            <h4 className="font-bold text-text text-sm flex items-center gap-2">
              <span>📡</span> The "Harvest Now, Decrypt Later" (HNDL) Threat
            </h4>
            <p>
              Nation-state adversaries and malicious organizations are currently recording and archiving vast amounts of encrypted internet communications (diplomatic cables, medical records, intellectual property, critical infrastructure secrets).
            </p>
            <p>
              Although they cannot decrypt this traffic today using classical supercomputers, the moment a cryptanalytically relevant quantum computer (CRQC) running Shor's algorithm emerges in 5 to 15 years, every recorded session protected solely by RSA, ECDH, or Diffie-Hellman will be decrypted instantly in retrospective batch operations.
            </p>
          </div>

          <div className="space-y-3">
            <h4 className="font-bold text-text text-sm flex items-center gap-2">
              <span>🔐</span> The Hybrid Advantage: Belt and Suspenders
            </h4>
            <p>
              No single algorithm is guaranteed to be unbreakable forever. ML-KEM is based on lattice problems (Module-LWE) that have withstood intense classical and quantum cryptanalysis, but mathematically unproven assumptions remain. Conversely, BB84 QKD offers information-theoretic security rooted in the laws of quantum physics, but requires specialized optical infrastructure.
            </p>
            <p>
              By combining both with <strong>HKDF-SHA256</strong>, the resulting session key remains secure if <em>either</em> the mathematical hardness of ML-KEM holds <em>or</em> the physical guarantees of BB84 hold. An adversary must simultaneously break quantum physics AND solve high-dimensional lattice mathematics.
            </p>
          </div>
        </div>

        {/* Live Empirical Metrics Comparison */}
        {compareStats && (
          <div className="mt-4 pt-4 border-t border-border">
            <h4 className="text-xs font-bold text-text uppercase tracking-wider mb-3">
              Empirical Performance Footprint (Measured on Local Host)
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {['classical', 'pqc', 'qkd', 'hybrid'].map((m) => {
                const stat = compareStats[m];
                if (!stat) return null;
                const isHybrid = m === 'hybrid';
                return (
                  <div
                    key={m}
                    className={`p-3 rounded-lg border text-xs ${
                      isHybrid
                        ? 'bg-hybrid/10 border-hybrid shadow-sm'
                        : 'bg-surface-2 border-border'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold uppercase font-mono text-text">{m}</span>
                      {isHybrid && <span className="badge bg-hybrid text-surface text-[10px] font-bold">Best</span>}
                    </div>
                    <div className="space-y-1 font-mono text-text-dim text-[11px]">
                      <div>Time: <strong className="text-text">{stat.total_ms} ms</strong></div>
                      <div>Bytes: <strong className="text-text">{stat.bytes_exchanged} B</strong></div>
                      <div>Steps: <strong className="text-text">{stat.step_count}</strong></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
