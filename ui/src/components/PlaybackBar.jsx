import { useEffect, useCallback, useMemo } from 'react';
import useRunStore from '../store/useRunStore';

export default function PlaybackBar() {
  const {
    events, playbackIndex, playing, speed, presentationMode,
    next, back, togglePlay, pause, setSpeed, setPresentationMode, reset,
  } = useRunStore();

  const steps = useMemo(() => events.filter((e) => e.type === 'step'), [events]);
  const total = steps.length;
  const hasEvents = events.length > 0;

  // Auto-play timer
  useEffect(() => {
    if (!playing) return;
    if (playbackIndex >= total - 1) {
      pause();
      return;
    }
    const delay = 800 / speed;
    const timer = setTimeout(next, delay);
    return () => clearTimeout(timer);
  }, [playing, playbackIndex, speed, total, next, pause]);

  // Keyboard shortcuts
  const handleKey = useCallback((e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
    if (e.key === 'ArrowRight') { e.preventDefault(); next(); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); back(); }
    if (e.key === ' ') { e.preventDefault(); togglePlay(); }
  }, [next, back, togglePlay]);

  useEffect(() => {
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [handleKey]);

  if (!hasEvents) return null;

  const current = playbackIndex + 1;
  const currentStep = playbackIndex >= 0 && playbackIndex < steps.length ? steps[playbackIndex] : null;

  return (
    <div className="card-sm flex flex-wrap items-center gap-3">
      <button className="btn-secondary text-sm" onClick={back} disabled={playbackIndex <= 0}>
        ◀ Back
      </button>
      <button className="btn-primary text-sm" onClick={next} disabled={playbackIndex >= total - 1}>
        Next ▶
      </button>
      <button className="btn-secondary text-sm" onClick={togglePlay}>
        {playing ? '⏸ Pause' : '▶ Play'}
      </button>

      <div className="flex items-center gap-2 text-xs text-text-dim">
        <span>Speed:</span>
        <input
          type="range" min="0.5" max="3" step="0.25"
          value={speed} onChange={(e) => setSpeed(parseFloat(e.target.value))}
          className="w-20 accent-alice"
        />
        <span className="font-mono">{speed}x</span>
      </div>

      <label className="flex items-center gap-1 text-xs text-text-dim cursor-pointer">
        <input
          type="checkbox" checked={presentationMode}
          onChange={(e) => setPresentationMode(e.target.checked)}
          className="accent-alice"
        />
        📺 Presentation
      </label>

      <div className="ml-auto flex items-center gap-2">
        <span className="text-xs font-mono text-text-dim">
          Step {current}/{total}
        </span>
        {currentStep && (
          <span className="text-xs text-alice font-medium">
            {currentStep.title || currentStep.id}
          </span>
        )}
        <button className="text-xs text-text-dim hover:text-eve cursor-pointer ml-2" onClick={reset}>
          ✕ Reset
        </button>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1.5 bg-surface-3 rounded-full mt-1">
        <div
          className="h-full bg-alice rounded-full transition-all duration-300"
          style={{ width: `${total > 0 ? (current / total) * 100 : 0}%` }}
        />
      </div>
    </div>
  );
}
