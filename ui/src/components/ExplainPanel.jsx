import { useState } from 'react';
import useRunStore from '../store/useRunStore';
import { STEP_DESCRIPTIONS } from '../content/stepContent';

export default function ExplainPanel({ stepId, content }) {
  const [open, setOpen] = useState(false);
  const presentationMode = useRunStore((s) => s.presentationMode);

  const resolvedContent = content || (stepId ? STEP_DESCRIPTIONS[stepId] : null);

  if (!resolvedContent) return null;

  return (
    <div className="mt-3 text-sm">
      <p className={`text-text-dim ${presentationMode ? 'text-base font-medium' : ''}`}>
        💡 {resolvedContent.simple}
      </p>
      {!presentationMode && (
        <button
          type="button"
          className="text-xs text-alice mt-1 hover:underline cursor-pointer flex items-center gap-1"
          onClick={() => setOpen(!open)}
        >
          <span>{open ? '▾' : '▸'}</span>
          <span>{open ? 'Hide technical details' : 'Technical details'}</span>
        </button>
      )}
      {open && !presentationMode && (
        <p className="text-xs text-text-dim mt-1.5 pl-3 border-l-2 border-alice/50 leading-relaxed font-mono">
          {resolvedContent.technical}
        </p>
      )}
    </div>
  );
}
