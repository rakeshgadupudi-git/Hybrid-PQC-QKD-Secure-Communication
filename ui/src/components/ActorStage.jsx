import { motion } from 'framer-motion';

export default function ActorStage({ step, eveActive }) {
  if (!step) return null;

  const actor = step.actor || 'system';
  const isEve = eveActive && ['bb84_transmit'].includes(step.id);

  return (
    <div className="flex items-center justify-center gap-4 py-3 px-4 rounded-lg bg-surface-2/50">
      {/* Alice */}
      <div className={`text-center ${actor === 'alice' ? 'ring-2 ring-alice rounded-lg p-2' : 'p-2 opacity-60'}`}>
        <div className="text-2xl">👩</div>
        <div className="text-xs font-medium text-alice">Alice</div>
      </div>

      {/* Channel / Arrow */}
      <div className="flex-1 relative flex items-center justify-center">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t-2 border-dashed border-border" />
        </div>
        {/* Animated packet */}
        <motion.div
          className={`relative z-10 px-3 py-1 rounded-full text-xs font-mono ${
            isEve ? 'bg-eve/20 text-eve border border-eve' : 'bg-alice/20 text-alice border border-alice/50'
          }`}
          initial={{ x: -60, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.4, type: 'spring' }}
        >
          {step.id?.replace(/_/g, ' ') || 'data'}
        </motion.div>

        {/* Eve indicator */}
        {isEve && (
          <motion.div
            className="absolute -top-6 left-1/2 -translate-x-1/2 text-center"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
          >
            <div className="text-xl pulse-red inline-block rounded-full">🕵️</div>
            <div className="text-xs text-eve font-bold">Eve intercepting!</div>
          </motion.div>
        )}
      </div>

      {/* Bob */}
      <div className={`text-center ${actor === 'bob' ? 'ring-2 ring-bob rounded-lg p-2' : 'p-2 opacity-60'}`}>
        <div className="text-2xl">👨</div>
        <div className="text-xs font-medium text-bob">Bob</div>
      </div>
    </div>
  );
}
