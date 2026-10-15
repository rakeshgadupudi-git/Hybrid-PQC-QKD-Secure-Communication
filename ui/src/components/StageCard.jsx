import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import QubitTable from './QubitTable';
import QberGauge from './QberGauge';
import KeyFunnel from './KeyFunnel';
import SizeCompare from './SizeCompare';
import KeyMixer from './KeyMixer';
import FingerprintBadge from './FingerprintBadge';
import ExplainPanel from './ExplainPanel';

const STAGE_TITLES = {
  quantum_key: '1. Quantum Key Exchange (BB84)',
  eavesdropper_check: '2. Eavesdropper Check & Clean-up',
  pq_key: '3. Post-Quantum Key Exchange (ML-KEM)',
  hybrid_mix: '4. Hybrid Key Derivation (HKDF)',
  confirm: '5. Key Confirmation',
  secure_chat: '6. Secure Authenticated Chat (AES-256-GCM)',
};

const STAGE_DESCRIPTIONS = {
  quantum_key: 'Alice & Bob exchange photons in random bases; eavesdropping introduces unavoidable disturbance.',
  eavesdropper_check: 'Sample verification calculates QBER. If <11%, error correction and privacy amplification distill a pristine key.',
  pq_key: 'Lattice-based ML-KEM generates a quantum-safe shared secret immune to Shor’s algorithm.',
  hybrid_mix: 'HKDF blends the quantum key, post-quantum key, and transcript hash into a defense-in-depth session key.',
  confirm: 'Mutual HMAC exchange confirms both peers derived identical session keys before transmitting application data.',
  secure_chat: 'Messages are protected with authenticated AES-256-GCM, sequence nonces, and replay mitigation.',
};

export default function StageCard({
  stageId,
  stageSteps = [],
  currentStep,
  visibleSteps = [],
  aborted = false,
  abortReason = '',
}) {
  const [userExpanded, setUserExpanded] = useState(null);

  const title = STAGE_TITLES[stageId] || stageId;
  const desc = STAGE_DESCRIPTIONS[stageId] || '';

  // Calculate status of this stage
  const stepIds = stageSteps.map((s) => s.id);
  const visibleStageSteps = visibleSteps.filter((s) => stepIds.includes(s.id));
  const hasCurrentStep = currentStep && stepIds.includes(currentStep.id);
  const isDone = !hasCurrentStep && visibleStageSteps.length === stageSteps.length && stageSteps.length > 0;
  const isAbortedInStage = aborted && hasCurrentStep;
  const isPending = visibleStageSteps.length === 0;

  // If user explicitly clicked toggle, use userExpanded; otherwise expand if current or aborted-in-stage
  const isExpanded = userExpanded !== null ? userExpanded : (hasCurrentStep || isAbortedInStage);

  // Active step to display inside card
  const activeStep = hasCurrentStep
    ? currentStep
    : visibleStageSteps[visibleStageSteps.length - 1] || stageSteps[0];

  const renderVisual = () => {
    if (!activeStep) return null;
    const { id, data } = activeStep;

    switch (id) {
      case 'bb84_prepare':
        return <QubitTable data={data} type="prepare" />;
      case 'bb84_transmit':
        return <QubitTable data={data} type="transmit" />;
      case 'bb84_measure':
        return <QubitTable data={data} type="measure" />;
      case 'bb84_sift':
        return <QubitTable data={data} type="sift" />;
      case 'bb84_qber':
        return (
          <div className="flex flex-col items-center">
            <QberGauge qber={data?.qber} threshold={data?.threshold || 0.11} />
            <div className="text-xs text-center mt-2 font-mono">
              Sample: {data?.sample_size} qubits | Decision:{' '}
              <span className={data?.decision === 'abort' ? 'text-eve font-bold' : 'text-bob font-bold'}>
                {data?.decision?.toUpperCase()}
              </span>
            </div>
          </div>
        );
      case 'bb84_error_correction':
        return (
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="p-2 bg-surface-2 rounded border border-border">
                <div className="text-text-dim">Errors Fixed</div>
                <div className="font-mono font-bold text-bob">{data?.errors_fixed ?? 0}</div>
              </div>
              <div className="p-2 bg-surface-2 rounded border border-border">
                <div className="text-text-dim">Cascade Passes</div>
                <div className="font-mono font-bold text-text">{data?.passes ?? 0}</div>
              </div>
              <div className="p-2 bg-surface-2 rounded border border-border">
                <div className="text-text-dim">Leaked Bits</div>
                <div className="font-mono font-bold text-amber-400">{data?.parity_bits_leaked ?? 0}</div>
              </div>
            </div>
          </div>
        );
      case 'bb84_privacy_amp':
        return (
          <div className="space-y-3">
            <KeyFunnel funnel={data?.funnel} />
            {data?.qkd_fingerprint && (
              <div className="flex items-center justify-between p-2.5 bg-qkd/10 border border-qkd/30 rounded-lg text-xs">
                <span className="font-semibold text-qkd">Distilled QKD Key:</span>
                <FingerprintBadge value={data.qkd_fingerprint} label="QKD" />
              </div>
            )}
          </div>
        );
      case 'mlkem_keygen':
      case 'mlkem_encaps':
      case 'mlkem_decaps':
        return <SizeCompare stepData={data} currentStepId={id} />;
      case 'hkdf_combine':
        return <KeyMixer data={data} />;
      case 'key_confirm':
        return (
          <div className="p-3 bg-surface-2 rounded-lg border border-border space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-text-dim">Alice Confirmation Tag:</span>
              <FingerprintBadge value={data?.alice_tag_fingerprint} label="Alice HMAC" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-text-dim">Bob Confirmation Tag:</span>
              <FingerprintBadge value={data?.bob_tag_fingerprint} label="Bob HMAC" />
            </div>
            <div className="pt-2 border-t border-border flex items-center justify-between">
              <span className="text-text-dim">Handshake Finalized:</span>
              {data?.ok ? (
                <span className="badge bg-emerald-500/20 text-emerald-400 font-bold">
                  ✓ Confirmed Identical
                </span>
              ) : (
                <span className="badge bg-rose-500/20 text-rose-400 font-bold">
                  ✗ Confirmation Failed
                </span>
              )}
            </div>
          </div>
        );
      case 'secure_chat':
        return (
          <div className="p-3 bg-surface-2 rounded-lg border border-border space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-text-dim">Ciphertext Hex Preview:</span>
              <span className="font-mono text-amber-400">{data?.ciphertext_hex_preview}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-text-dim">Plaintext Decrypted:</span>
              <span className="text-bob font-semibold">"{data?.decrypted}"</span>
            </div>
          </div>
        );
      default:
        return (
          <pre className="text-xs font-mono bg-surface-2 p-2 rounded overflow-x-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        );
    }
  };

  return (
    <div
      className={`card transition-all duration-300 border ${
        isAbortedInStage
          ? 'border-rose-500 shadow-rose-500/20 shadow-lg bg-surface'
          : hasCurrentStep
          ? 'border-alice shadow-alice/20 shadow-lg bg-surface ring-1 ring-alice/40'
          : isDone
          ? 'border-emerald-500/30 bg-surface/80'
          : 'border-border/50 bg-surface/30 opacity-60'
      }`}
    >
      {/* Header bar */}
      <div
        onClick={() => setUserExpanded(!isExpanded)}
        className="flex items-center justify-between cursor-pointer select-none"
      >
        <div className="flex items-center gap-3">
          <span className="text-lg">
            {isAbortedInStage ? '❌' : isDone ? '✅' : hasCurrentStep ? '⚡' : '⏳'}
          </span>
          <div>
            <h4 className="text-sm font-bold text-text flex items-center gap-2">
              {title}
              {hasCurrentStep && (
                <span className="badge bg-alice/20 text-alice font-mono text-[10px]">
                  STEP {activeStep?.step || ''}: {activeStep?.id}
                </span>
              )}
            </h4>
            <p className="text-xs text-text-dim">{desc}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {activeStep?.duration_ms != null && (
            <span className="text-[11px] font-mono text-text-dim">
              {activeStep.duration_ms.toFixed(1)} ms
            </span>
          )}
          <span className="text-xs text-text-dim">{isExpanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {/* Abort banner inside card if aborted at this stage */}
      {isAbortedInStage && (
        <div className="mt-3 p-3 bg-rose-500/10 border border-rose-500/40 rounded-lg text-xs text-rose-400 font-semibold flex items-center gap-2">
          <span>🚨</span> Eavesdropper detected! Handshake aborted: {abortReason || 'QBER above threshold'}
        </div>
      )}

      {/* Expanded intermediate results content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 pt-4 border-t border-border space-y-4"
          >
            {/* Step badges selector within stage if multiple steps completed */}
            {visibleStageSteps.length > 1 && (
              <div className="flex flex-wrap gap-1.5 pb-2">
                {visibleStageSteps.map((st) => (
                  <span
                    key={st.id}
                    className={`badge cursor-default ${
                      st.id === activeStep?.id
                        ? 'bg-alice text-white font-bold'
                        : 'bg-surface-3 text-text-dim'
                    }`}
                  >
                    {st.title || st.id}
                  </span>
                ))}
              </div>
            )}

            {/* Visual widget */}
            {renderVisual()}

            {/* Plain English and technical explanation */}
            {activeStep && <ExplainPanel stepId={activeStep.id} />}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
