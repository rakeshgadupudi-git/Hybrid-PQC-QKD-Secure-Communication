import { useMemo } from 'react';
import useRunStore from '../store/useRunStore';
import SetupPanel from '../components/SetupPanel';
import PlaybackBar from '../components/PlaybackBar';
import ActorStage from '../components/ActorStage';
import StageCard from '../components/StageCard';
import ChatPanel from '../components/ChatPanel';
import ProtectionScorecard from '../components/ProtectionScorecard';

const STAGE_ORDER = [
  'quantum_key',
  'eavesdropper_check',
  'pq_key',
  'hybrid_mix',
  'confirm',
  'secure_chat',
];

export default function LiveHandshake() {
  const {
    events,
    plan,
    playbackIndex,
    eveOn,
    mode,
    aborted,
    abortReason,
    error,
  } = useRunStore();

  const stepEvents = useMemo(() => events.filter((e) => e.type === 'step'), [events]);
  const scorecardEvent = useMemo(() => events.find((e) => e.type === 'scorecard'), [events]);
  const currentStep = playbackIndex >= 0 && playbackIndex < stepEvents.length ? stepEvents[playbackIndex] : null;
  const visibleSteps = playbackIndex >= 0 ? stepEvents.slice(0, playbackIndex + 1) : [];

  // Group steps by stage
  const stageStepsMap = useMemo(() => {
    const map = {};
    STAGE_ORDER.forEach((s) => {
      map[s] = [];
    });

    if (plan) {
      plan.forEach((stage) => {
        map[stage.id] = stage.steps || [];
      });
    } else {
      stepEvents.forEach((s) => {
        if (!map[s.stage]) map[s.stage] = [];
        if (!map[s.stage].some((existing) => existing.id === s.id)) {
          map[s.stage].push(s);
        }
      });
    }
    return map;
  }, [plan, stepEvents]);

  // Find chat step data if completed
  const chatStep = stepEvents.find((s) => s.id === 'secure_chat');
  const chatData = chatStep?.data;

  // Has run finished or aborted
  const isFinished = events.length > 0 && (playbackIndex >= stepEvents.length - 1 || aborted);

  return (
    <div className="space-y-6">
      {/* 1. Setup Panel */}
      <SetupPanel />

      {/* Error alert if WebSocket or API failed */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500 rounded-xl text-rose-400 text-sm flex items-center gap-3">
          <span className="text-xl">⚠️</span>
          <div>
            <strong>Handshake Connection Error:</strong> {error}
            <div className="text-xs text-text-dim mt-0.5">
              Make sure the backend is running with: <code>uvicorn api.main:app --port 8000</code>
            </div>
          </div>
        </div>
      )}

      {/* 2. Playback & Pipeline */}
      {events.length > 0 && (
        <div className="space-y-6">
          <PlaybackBar />

          {/* Actor Stage animation */}
          <ActorStage step={currentStep} eveActive={eveOn} />

          {/* Abort full-width warning if Eve triggered abort */}
          {aborted && currentStep?.id === 'bb84_qber' && (
            <div className="p-4 bg-rose-500/15 border-2 border-rose-500 rounded-xl text-rose-400 flex items-center justify-between gap-3 shadow-lg shadow-rose-500/10 animate-pulse">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🚨</span>
                <div>
                  <h4 className="font-bold text-base">Eavesdropper Detected! Handshake Aborted</h4>
                  <p className="text-xs text-rose-300">
                    {abortReason || 'QBER exceeded the 11% quantum threshold. No keys were established.'}
                  </p>
                </div>
              </div>
              <span className="badge bg-rose-500 text-white font-mono text-xs px-2.5 py-1">
                SECURITY HALT
              </span>
            </div>
          )}

          {/* Pipeline Stage Cards */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-text-dim uppercase tracking-wider">
              Protocol Pipeline Stages
            </h3>

            {STAGE_ORDER.map((stageId) => {
              const steps = stageStepsMap[stageId] || [];
              if (steps.length === 0 && plan) return null; // Stage not in current mode

              return (
                <StageCard
                  key={stageId}
                  stageId={stageId}
                  stageSteps={steps}
                  currentStep={currentStep}
                  visibleSteps={visibleSteps}
                  aborted={aborted}
                  abortReason={abortReason}
                />
              );
            })}
          </div>

          {/* 3. Result: Chat Panel */}
          {chatData && (visibleSteps.some((s) => s.id === 'secure_chat') || isFinished) && (
            <div className="pt-2">
              <ChatPanel chatData={chatData} mode={mode} />
            </div>
          )}

          {/* 4. Protection Scorecard */}
          {scorecardEvent && isFinished && (
            <div className="pt-2">
              <ProtectionScorecard scorecard={scorecardEvent.data} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
