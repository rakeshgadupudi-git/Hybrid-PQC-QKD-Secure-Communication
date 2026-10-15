import { motion } from 'framer-motion';

export default function QberGauge({ qber, threshold = 0.11 }) {
  if (qber == null) return null;

  const pct = Math.min(qber, 0.5) / 0.5; // normalize to 0-1 for 0-50% range
  const threshPct = threshold / 0.5;
  const isAbort = qber > threshold;
  const angle = -90 + pct * 180; // -90 to 90 degrees
  const threshAngle = -90 + threshPct * 180;

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-48 h-28 overflow-hidden">
        {/* Background arc */}
        <svg viewBox="0 0 200 110" className="w-full h-full">
          {/* Gauge background */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="currentColor"
            strokeWidth="12"
            className="text-surface-3"
            strokeLinecap="round"
          />
          {/* Safe zone (green) */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="#22c55e"
            strokeWidth="12"
            strokeDasharray={`${threshPct * 251} 251`}
            strokeLinecap="round"
            opacity="0.3"
          />
          {/* Danger zone */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="#ef4444"
            strokeWidth="12"
            strokeDasharray={`${251} 251`}
            strokeDashoffset={`-${threshPct * 251}`}
            strokeLinecap="round"
            opacity="0.2"
          />
          {/* Threshold marker */}
          <line
            x1={100 + 80 * Math.cos((threshAngle - 90) * Math.PI / 180)}
            y1={100 + 80 * Math.sin((threshAngle - 90) * Math.PI / 180)}
            x2={100 + 65 * Math.cos((threshAngle - 90) * Math.PI / 180)}
            y2={100 + 65 * Math.sin((threshAngle - 90) * Math.PI / 180)}
            stroke="#f59e0b"
            strokeWidth="3"
          />
          <text
            x={100 + 55 * Math.cos((threshAngle - 90) * Math.PI / 180)}
            y={100 + 55 * Math.sin((threshAngle - 90) * Math.PI / 180)}
            fontSize="8"
            fill="#f59e0b"
            textAnchor="middle"
          >
            {(threshold * 100).toFixed(0)}%
          </text>
          {/* Needle */}
          <motion.line
            x1="100" y1="100"
            x2={100 + 70 * Math.cos((angle - 90) * Math.PI / 180)}
            y2={100 + 70 * Math.sin((angle - 90) * Math.PI / 180)}
            stroke={isAbort ? '#ef4444' : '#22c55e'}
            strokeWidth="3"
            strokeLinecap="round"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          />
          <circle cx="100" cy="100" r="4" fill={isAbort ? '#ef4444' : '#22c55e'} />
        </svg>
      </div>
      <div className={`text-center font-mono text-lg font-bold ${isAbort ? 'text-eve' : 'text-bob'}`}>
        QBER: {(qber * 100).toFixed(2)}%
      </div>
      <div className={`text-xs ${isAbort ? 'text-eve' : 'text-bob'}`}>
        {isAbort ? '🚨 Above threshold — eavesdropper detected!' : '✅ Below threshold — channel is safe'}
      </div>
    </div>
  );
}
