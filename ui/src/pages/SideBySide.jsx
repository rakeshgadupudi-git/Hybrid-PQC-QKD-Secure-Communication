import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { postRunPair } from '../api/client';
import StageCard from '../components/StageCard';
import ProtectionScorecard from '../components/ProtectionScorecard';

const STAGE_ORDER = [
  'quantum_key',
  'eavesdropper_check',
  'pq_key',
  'hybrid_mix',
  'confirm',
  'secure_chat',
];

export default function SideBySide() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pairData, setPairData] = useState(null);
  const [playbackIndex, setPlaybackIndex] = useState(0);
  const [qubits, setQubits] = useState(2048);
  const [attackEveRate, setAttackEveRate] = useState(1.0);

  const fetchPair = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await postRunPair({
        mode: 'hybrid',
        qubits,
        attack_eve_rate: attackEveRate,
        message: 'Hello Bob, confidential hybrid handshake message.',
      });
      setPairData(res);
      setPlaybackIndex(0);
    } catch (err) {
      setError(err.message || 'Failed to execute pair comparison run');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPair();
  }, []);

  const normalSteps = useMemo(
    () => pairData?.normal?.filter((e) => e.type === 'step') || [],
    [pairData]
  );
  const attackSteps = useMemo(
    () => pairData?.attack?.filter((e) => e.type === 'step') || [],
    [pairData]
  );
  const normalScorecard = useMemo(
    () => pairData?.normal?.find((e) => e.type === 'scorecard')?.data,
    [pairData]
  );
  const attackScorecard = useMemo(
    () => pairData?.attack?.find((e) => e.type === 'scorecard')?.data,
    [pairData]
  );
  const attackAborted = useMemo(
    () => pairData?.attack?.find((e) => e.type === 'aborted')?.data,
    [pairData]
  );

  const maxSteps = Math.max(normalSteps.length, attackSteps.length);
  const currentNormalStep = normalSteps[playbackIndex] || null;
  const currentAttackStep = attackSteps[playbackIndex] || null;

  const normalVisible = normalSteps.slice(0, playbackIndex + 1);
  const attackVisible = attackSteps.slice(0, playbackIndex + 1);

  const divergesStepNumber = pairData?.diverges_at_step || 6;
  const isDivergingStep = currentNormalStep?.step === divergesStepNumber;

  const groupStepsByStage = (steps) => {
    const map = {};
    STAGE_ORDER.forEach((s) => {
      map[s] = [];
    });
    steps.forEach((s) => {
      if (!map[s.stage]) map[s.stage] = [];
      if (!map[s.stage].some((existing) => existing.id === s.id)) {
        map[s.stage].push(s);
      }
    });
    return map;
  };

  const normalStageMap = useMemo(() => groupStepsByStage(normalSteps), [normalSteps]);
  const attackStageMap = useMemo(() => groupStepsByStage(attackSteps), [attackSteps]);

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="card space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2 text-text">
              <span>⚔️</span> Side-by-Side: Normal vs Under Attack
            </h2>
            <p className="text-xs text-text-dim">
              Both runs use identical PRNG seeds and quantum channels. The only difference is Eve intercepting qubits.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-text-dim">
              <span>Eve Rate:</span>
              <select
                className="input py-1 text-xs"
                value={attackEveRate}
                onChange={(e) => setAttackEveRate(parseFloat(e.target.value))}
              >
                <option value={0.5}>50% Intercept</option>
                <option value={1.0}>100% Intercept</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5 text-xs text-text-dim">
              <span>Qubits:</span>
              <select
                className="input py-1 text-xs"
                value={qubits}
                onChange={(e) => setQubits(parseInt(e.target.value))}
              >
                <option value={1024}>1,024</option>
                <option value={2048}>2,048</option>
                <option value={4096}>4,096</option>
              </select>
            </div>

            <button
              onClick={fetchPair}
              disabled={loading}
              className="btn-primary text-xs flex items-center gap-1.5"
            >
              <span>🔄</span> {loading ? 'Running pair...' : 'Re-run Comparison'}
            </button>
          </div>
        </div>

        {/* Unified Playback Bar */}
        {maxSteps > 0 && (
          <div className="pt-3 border-t border-border flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <button
                className="btn-secondary text-xs"
                onClick={() => setPlaybackIndex((p) => Math.max(0, p - 1))}
                disabled={playbackIndex <= 0}
              >
                ◀ Back
              </button>
              <button
                className="btn-primary text-xs"
                onClick={() => setPlaybackIndex((p) => Math.min(maxSteps - 1, p + 1))}
                disabled={playbackIndex >= maxSteps - 1}
              >
                Next ▶
              </button>
              <span className="text-xs font-mono text-text-dim ml-2">
                Step {playbackIndex + 1} of {maxSteps}
              </span>
            </div>

            {/* Divergence Notification */}
            {isDivergingStep && (
              <motion.div
                initial={{ scale: 0.9 }}
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
                className="badge bg-rose-500/20 text-rose-400 border border-rose-500/50 py-1 px-3 text-xs font-semibold flex items-center gap-2"
              >
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                ⚡ PROTOCOL DIVERGES HERE (Step {divergesStepNumber})
              </motion.div>
            )}

            <div className="text-xs text-text-dim">
              {currentNormalStep ? currentNormalStep.title : 'Complete'}
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500 rounded-xl text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Two Column Layout */}
      {pairData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Normal Column */}
          <div className="space-y-4">
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/40 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">🛡️</span>
                <div>
                  <h3 className="font-bold text-sm text-emerald-400">Normal Channel (No Eve)</h3>
                  <p className="text-[11px] text-text-dim">Handshake completes through all 6 stages smoothly</p>
                </div>
              </div>
              <span className="badge bg-emerald-500/20 text-emerald-400 font-mono text-xs">
                SUCCESS
              </span>
            </div>

            {/* Stage Cards for Normal */}
            <div className="space-y-3">
              {STAGE_ORDER.map((stageId) => {
                const steps = normalStageMap[stageId] || [];
                if (steps.length === 0) return null;
                return (
                  <StageCard
                    key={`normal-${stageId}`}
                    stageId={stageId}
                    stageSteps={steps}
                    currentStep={currentNormalStep}
                    visibleSteps={normalVisible}
                    aborted={false}
                  />
                );
              })}
            </div>

            {/* Normal Scorecard */}
            {normalScorecard && (
              <div className="pt-2">
                <ProtectionScorecard
                  scorecard={normalScorecard}
                  title="Normal Protection Scorecard"
                />
              </div>
            )}
          </div>

          {/* Under Attack Column */}
          <div className="space-y-4">
            <div className="p-3 bg-rose-500/10 border border-rose-500/40 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">🕵️</span>
                <div>
                  <h3 className="font-bold text-sm text-rose-400">
                    Under Attack (Eve {Math.round(attackEveRate * 100)}%)
                  </h3>
                  <p className="text-[11px] text-text-dim">
                    Eve intercepts qubits; detected at Step {divergesStepNumber}
                  </p>
                </div>
              </div>
              <span className="badge bg-rose-500/20 text-rose-400 font-mono text-xs">
                ABORTED
              </span>
            </div>

            {/* Stage Cards for Attack */}
            <div className="space-y-3">
              {STAGE_ORDER.map((stageId) => {
                const steps = attackStageMap[stageId] || [];
                if (steps.length === 0) return null;
                return (
                  <StageCard
                    key={`attack-${stageId}`}
                    stageId={stageId}
                    stageSteps={steps}
                    currentStep={currentAttackStep}
                    visibleSteps={attackVisible}
                    aborted={true}
                    abortReason={attackAborted?.reason}
                  />
                );
              })}
            </div>

            {/* Attack Scorecard */}
            {attackScorecard && (
              <div className="pt-2">
                <ProtectionScorecard
                  scorecard={attackScorecard}
                  title="Attack Lab Scorecard"
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
