import { motion } from 'framer-motion';
import FingerprintBadge from './FingerprintBadge';

const ALGORITHMS = [
  { name: 'X25519 (ECDH)', type: 'Classical', pkBytes: 32, ctBytes: 32, quantumSafe: false, color: '#9ca3af' },
  { name: 'RSA-3072', type: 'Classical', pkBytes: 384, ctBytes: 384, quantumSafe: false, color: '#ef4444' },
  { name: 'ML-KEM-512', type: 'Post-Quantum (NIST 1)', pkBytes: 800, ctBytes: 768, quantumSafe: true, color: '#f97316' },
  { name: 'ML-KEM-768', type: 'Post-Quantum (NIST 3)', pkBytes: 1184, ctBytes: 1088, quantumSafe: true, color: '#f97316' },
  { name: 'ML-KEM-1024', type: 'Post-Quantum (NIST 5)', pkBytes: 1568, ctBytes: 1568, quantumSafe: true, color: '#f97316' },
];

export default function SizeCompare({ stepData, currentStepId }) {
  const maxBytes = 1600;

  return (
    <div className="space-y-4">
      {stepData && (
        <div className="p-3 bg-surface-2 rounded-lg border border-border flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-pqc">Active ML-KEM Level:</span>
            <span className="badge bg-pqc/20 text-pqc font-mono font-bold">
              ML-KEM-{stepData.level || '768'}
            </span>
          </div>

          {stepData.ek_bytes && (
            <div>
              <span className="text-text-dim">Public Key (ek): </span>
              <span className="font-mono font-semibold">{stepData.ek_bytes} B</span>
            </div>
          )}

          {stepData.ct_bytes && (
            <div>
              <span className="text-text-dim">Ciphertext (ct): </span>
              <span className="font-mono font-semibold">{stepData.ct_bytes} B</span>
            </div>
          )}

          {stepData.fingerprint_alice && (
            <div className="flex items-center gap-1.5">
              <span className="text-text-dim">Alice Secret:</span>
              <FingerprintBadge value={stepData.fingerprint_alice} label="Alice" />
            </div>
          )}

          {stepData.fingerprint_bob && (
            <div className="flex items-center gap-1.5">
              <span className="text-text-dim">Bob Secret:</span>
              <FingerprintBadge value={stepData.fingerprint_bob} label="Bob" />
              {stepData.match && <span className="text-bob font-bold ml-1">✓ Match</span>}
            </div>
          )}
        </div>
      )}

      {/* Bar visual comparing sizes */}
      <div className="space-y-2.5">
        <div className="text-xs font-semibold text-text-dim flex justify-between">
          <span>Algorithm Public Key / Ciphertext Footprint Comparison</span>
          <span>Bytes</span>
        </div>

        {ALGORITHMS.map((algo) => {
          const isSelected = stepData?.level ? algo.name.includes(String(stepData.level)) : algo.name.includes('768');
          const widthPct = Math.round((algo.pkBytes / maxBytes) * 100);

          return (
            <div
              key={algo.name}
              className={`p-2.5 rounded-lg border transition-all text-xs ${
                isSelected ? 'bg-pqc/10 border-pqc shadow-sm' : 'bg-surface-2/60 border-border'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-semibold font-mono text-text">{algo.name}</span>
                  <span className={`badge ${algo.quantumSafe ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                    {algo.quantumSafe ? '🛡️ Quantum-Safe' : '⚠️ Broken by Shor'}
                  </span>
                  {isSelected && <span className="badge bg-pqc text-white font-bold">Current</span>}
                </div>
                <div className="font-mono text-text-dim">
                  PK: <strong className="text-text">{algo.pkBytes}B</strong> | CT: <strong className="text-text">{algo.ctBytes}B</strong>
                </div>
              </div>

              {/* Bar visualization */}
              <div className="w-full h-2 bg-surface-3 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${widthPct}%` }}
                  transition={{ duration: 0.6, ease: 'easeOut' }}
                  className="h-full rounded-full"
                  style={{ backgroundColor: algo.color }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="text-xs text-text-dim bg-surface-2/40 p-2.5 rounded-lg border border-border">
        💡 <strong>Post-Quantum Trade-off:</strong> ML-KEM uses lattice mathematics (Module-LWE) instead of discrete logarithms or factoring. While immune to Shor's algorithm, its public keys and ciphertexts are ~30x larger than ECDH (X25519).
      </div>
    </div>
  );
}
