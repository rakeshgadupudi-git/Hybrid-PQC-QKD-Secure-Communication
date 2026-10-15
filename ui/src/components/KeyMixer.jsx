import { motion } from 'framer-motion';
import FingerprintBadge from './FingerprintBadge';

export default function KeyMixer({ data }) {
  if (!data) return null;

  const {
    inputs = [],
    transcript_fingerprint,
    session_fingerprint_alice,
    session_fingerprint_bob,
    match,
  } = data;

  return (
    <div className="space-y-4">
      <div className="text-xs text-text-dim">
        Cryptographic Key Derivation Function (HKDF-SHA256) extracts entropy from all components and binds the transcript to prevent man-in-the-middle substitutions.
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
        {/* Input keys */}
        <div className="space-y-2">
          <div className="text-xs font-semibold text-text-dim uppercase tracking-wider">
            Input Key Material
          </div>
          {inputs.map((inp, idx) => {
            const isQkd = inp.name.toLowerCase().includes('qkd');
            const isPqc = inp.name.toLowerCase().includes('pqc');
            return (
              <motion.div
                key={inp.name}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.15 }}
                className={`p-2.5 rounded-lg border text-xs flex items-center justify-between ${
                  isQkd
                    ? 'bg-qkd/10 border-qkd/40'
                    : isPqc
                    ? 'bg-pqc/10 border-pqc/40'
                    : 'bg-surface-2 border-border'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span>{isQkd ? '⚛️' : isPqc ? '🛡️' : '🔑'}</span>
                  <span className="font-semibold uppercase">{inp.name}</span>
                </div>
                <FingerprintBadge value={inp.fingerprint} />
              </motion.div>
            );
          })}

          {transcript_fingerprint && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="p-2.5 rounded-lg border border-alice/30 bg-alice/10 text-xs flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <span>📜</span>
                <span className="font-semibold">Transcript Salt</span>
              </div>
              <FingerprintBadge value={transcript_fingerprint} />
            </motion.div>
          )}
        </div>

        {/* HKDF Mixer Core */}
        <div className="flex flex-col items-center justify-center p-4 bg-surface-2 rounded-xl border border-hybrid/30 relative">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 8, ease: 'linear' }}
            className="text-3xl mb-2"
          >
            ⚙️
          </motion.div>
          <div className="text-xs font-bold text-hybrid tracking-wide">HKDF-SHA256</div>
          <div className="text-[10px] text-text-dim text-center mt-1">
            Extract & Expand<br />(FIPS SP 800-56C)
          </div>
          <div className="text-[10px] text-emerald-400 font-mono mt-2 bg-surface-3 px-2 py-0.5 rounded">
            256-bit Session Key
          </div>
        </div>

        {/* Derived Output Key */}
        <div className="space-y-2">
          <div className="text-xs font-semibold text-text-dim uppercase tracking-wider">
            Derived Session Key
          </div>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="p-3 rounded-lg border border-hybrid bg-hybrid/10 text-xs space-y-2"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-hybrid">Alice Session:</span>
              <FingerprintBadge value={session_fingerprint_alice} label="Alice" />
            </div>

            <div className="flex items-center justify-between">
              <span className="font-semibold text-hybrid">Bob Session:</span>
              <FingerprintBadge value={session_fingerprint_bob} label="Bob" />
            </div>

            <div className="pt-2 border-t border-hybrid/20 flex items-center justify-between">
              <span className="text-text-dim">Cryptographic Agreement:</span>
              {match ? (
                <span className="badge bg-emerald-500/20 text-emerald-400 font-bold flex items-center gap-1">
                  <span>✓</span> Matching Keys
                </span>
              ) : (
                <span className="badge bg-rose-500/20 text-rose-400 font-bold">
                  ✗ Mismatch
                </span>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
