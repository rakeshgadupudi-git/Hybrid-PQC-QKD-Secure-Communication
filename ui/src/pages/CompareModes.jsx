import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { fetchCompare } from '../api/client';

const MODE_DETAILS = {
  classical: {
    name: 'Classical (X25519 / ECDH)',
    icon: '🔓',
    securityStatus: 'Vulnerable to Quantum Computers',
    securityColor: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
    threat: 'Harvest Now, Decrypt Later (HNDL). Shor’s algorithm on a quantum computer solves discrete logs in polynomial time.',
    keySizes: 'Public Key: 32 B | Shared Secret: 32 B',
    infrastructure: 'Standard IP networks, existing TLS 1.3 stacks',
    bestFor: 'Legacy systems with minimal bandwidth and no long-term security sensitivity.',
  },
  pqc: {
    name: 'Post-Quantum (ML-KEM-768)',
    icon: '🛡️',
    securityStatus: 'Post-Quantum Secure (NIST FIPS 203)',
    securityColor: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
    threat: 'Safe against quantum computers; however, relies on mathematical hardness assumptions (Module-LWE) without physical proof.',
    keySizes: 'Public Key: 1,184 B | Ciphertext: 1,088 B | Secret: 32 B',
    infrastructure: 'Pure software update over existing internet infrastructure',
    bestFor: 'General internet traffic, software applications requiring immediate post-quantum protection.',
  },
  qkd: {
    name: 'Quantum Key Distribution (BB84)',
    icon: '⚛️',
    securityStatus: 'Information-Theoretic Physical Security',
    securityColor: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
    threat: 'Immune to all computational power forever (quantum or classical). Limited by physical range and fiber repeaters.',
    keySizes: 'Transmits ~4,000 photons | Distills 256-bit symmetric key',
    infrastructure: 'Dedicated dark fiber or free-space optical channels, single-photon detectors',
    bestFor: 'High-value links (government, central banks, power grid backbones) within metropolitan range.',
  },
  hybrid: {
    name: 'Hybrid (BB84 + ML-KEM + HKDF)',
    icon: '🔐',
    securityStatus: 'Dual Defense-in-Depth (Gold Standard)',
    securityColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
    threat: 'Adversary must simultaneously break quantum mechanics AND solve lattice mathematical hardness.',
    keySizes: 'Combined HKDF extraction | 256-bit Session Key',
    infrastructure: 'Hybrid optical & classical IP channels with dual-handshake stack',
    bestFor: 'Mission-critical infrastructure with multi-decade confidentiality requirements.',
  },
};

export default function CompareModes() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchCompare();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to fetch comparison benchmarks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2 text-text">
            <span>📊</span> Architectural Mode Comparison
          </h2>
          <p className="text-sm text-text-dim mt-1">
            Comparing Classical (X25519), Post-Quantum (ML-KEM-768), Quantum (BB84), and Hybrid Key Exchange across live measured metrics.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="btn-secondary text-xs flex items-center gap-2 self-start"
        >
          <span>🔄</span> {loading ? 'Benchmarking...' : 'Re-run Comparison'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500 rounded-xl text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Grid of 4 Mode Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {['classical', 'pqc', 'qkd', 'hybrid'].map((key) => {
          const detail = MODE_DETAILS[key];
          const metrics = data ? data[key] : null;
          const isHybrid = key === 'hybrid';

          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className={`card flex flex-col justify-between space-y-4 border ${
                isHybrid ? 'border-hybrid ring-1 ring-hybrid/30 shadow-lg' : 'border-border'
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-2xl">{detail.icon}</span>
                  <span className="badge bg-surface-3 text-text font-mono text-[10px] uppercase">
                    {key}
                  </span>
                </div>

                <h3 className="font-bold text-sm text-text mt-2">{detail.name}</h3>

                <div className={`mt-2 p-2 rounded border text-[11px] font-semibold ${detail.securityColor}`}>
                  {detail.securityStatus}
                </div>

                {/* Measured Performance */}
                <div className="mt-3 p-2.5 bg-surface-2 rounded-lg border border-border space-y-1.5 text-xs font-mono">
                  <div className="text-[10px] text-text-dim uppercase tracking-wider font-sans font-bold">
                    Measured Execution
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-dim">Latency:</span>
                    <strong className="text-text">{metrics ? `${metrics.total_ms} ms` : '—'}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-dim">Wire Bytes:</span>
                    <strong className="text-text">{metrics ? `${metrics.bytes_exchanged} B` : '—'}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-dim">Handshake Steps:</span>
                    <strong className="text-text">{metrics ? metrics.step_count : '—'}</strong>
                  </div>
                </div>

                {/* Architectural Specs */}
                <div className="mt-3 space-y-2 text-xs text-text-dim">
                  <div>
                    <strong className="text-text">Key Footprint:</strong>
                    <p className="text-[11px]">{detail.keySizes}</p>
                  </div>
                  <div>
                    <strong className="text-text">Infrastructure:</strong>
                    <p className="text-[11px]">{detail.infrastructure}</p>
                  </div>
                  <div>
                    <strong className="text-text">Threat Assessment:</strong>
                    <p className="text-[11px]">{detail.threat}</p>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-border text-[11px] text-text-dim">
                <strong className="text-text">Ideal Use Case:</strong> {detail.bestFor}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Comprehensive Summary Table */}
      <div className="card space-y-3 overflow-x-auto">
        <h3 className="text-base font-bold text-text">
          Comprehensive Feature Matrix
        </h3>
        <table className="w-full text-xs text-left border-collapse">
          <thead>
            <tr className="border-b border-border text-text-dim">
              <th className="py-2.5 px-3">Mode</th>
              <th className="py-2.5 px-3">Theoretical Basis</th>
              <th className="py-2.5 px-3">Post-Quantum Safe</th>
              <th className="py-2.5 px-3">Information Theoretic</th>
              <th className="py-2.5 px-3">Requires Optical Link</th>
              <th className="py-2.5 px-3">Standardization Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40 font-mono">
            <tr>
              <td className="py-2.5 px-3 font-sans font-semibold text-text">Classical (X25519)</td>
              <td className="py-2.5 px-3">Elliptic Curves (Diffie-Hellman)</td>
              <td className="py-2.5 px-3 text-rose-400 font-bold">❌ Broken by Shor</td>
              <td className="py-2.5 px-3 text-rose-400">❌ No (Computational)</td>
              <td className="py-2.5 px-3 text-bob">❌ No (Software only)</td>
              <td className="py-2.5 px-3 font-sans text-text-dim">RFC 7748 (Mature)</td>
            </tr>
            <tr>
              <td className="py-2.5 px-3 font-sans font-semibold text-pqc">PQC (ML-KEM-768)</td>
              <td className="py-2.5 px-3">Module Learning with Errors (Lattices)</td>
              <td className="py-2.5 px-3 text-bob font-bold">✅ Yes (Quantum-Safe)</td>
              <td className="py-2.5 px-3 text-text-dim">❌ No (Computational)</td>
              <td className="py-2.5 px-3 text-bob">❌ No (Software only)</td>
              <td className="py-2.5 px-3 font-sans text-text-dim">NIST FIPS 203 (2024)</td>
            </tr>
            <tr>
              <td className="py-2.5 px-3 font-sans font-semibold text-qkd">QKD (BB84)</td>
              <td className="py-2.5 px-3">No-Cloning Theorem & Conjugate Bases</td>
              <td className="py-2.5 px-3 text-bob font-bold">✅ Yes (Physics-Based)</td>
              <td className="py-2.5 px-3 text-bob font-bold">✅ Yes (Information-Theoretic)</td>
              <td className="py-2.5 px-3 text-amber-400">⚠️ Yes (Single-Photon Fiber)</td>
              <td className="py-2.5 px-3 font-sans text-text-dim">ETSI GS QKD / ISO</td>
            </tr>
            <tr className="bg-hybrid/5">
              <td className="py-2.5 px-3 font-sans font-semibold text-hybrid">Hybrid (BB84+PQC)</td>
              <td className="py-2.5 px-3">Physical Quantum Laws + Lattice Hardness</td>
              <td className="py-2.5 px-3 text-bob font-bold">✅ Double Protected</td>
              <td className="py-2.5 px-3 text-bob font-bold">✅ Yes (via QKD branch)</td>
              <td className="py-2.5 px-3 text-amber-400">⚠️ For QKD channel only</td>
              <td className="py-2.5 px-3 font-sans text-text-dim">NIST / BSI Recommended</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
