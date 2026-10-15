import { motion } from 'framer-motion';

const STATUS_CONFIG = {
  active: {
    icon: '🛡️',
    label: 'ACTIVE',
    badgeClass: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
    cardBorder: 'border-emerald-500/30 bg-emerald-500/5',
  },
  triggered: {
    icon: '🚨',
    label: 'TRIGGERED (ATTACK CAUGHT)',
    badgeClass: 'bg-rose-500/20 text-rose-400 border-rose-500/40 animate-pulse',
    cardBorder: 'border-rose-500/50 bg-rose-500/10',
  },
  not_in_mode: {
    icon: '➖',
    label: 'NOT IN MODE',
    badgeClass: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    cardBorder: 'border-border/60 bg-surface/30 opacity-60',
  },
  failed: {
    icon: '❌',
    label: 'FAILED',
    badgeClass: 'bg-rose-600/30 text-rose-300 border-rose-600/50',
    cardBorder: 'border-rose-600 bg-rose-950/20',
  },
  not_reached: {
    icon: '⏭️',
    label: 'NOT REACHED (ABORTED)',
    badgeClass: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    cardBorder: 'border-border/60 bg-surface/30 opacity-50',
  },
};

export default function ProtectionScorecard({ scorecard, title = 'Handshake Protection Scorecard' }) {
  if (!scorecard || !scorecard.items || scorecard.items.length === 0) {
    return null;
  }

  const items = scorecard.items;
  const activeCount = items.filter((i) => i.status === 'active').length;
  const triggeredCount = items.filter((i) => i.status === 'triggered').length;

  return (
    <div className="card space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-3">
        <div>
          <h3 className="text-base font-bold flex items-center gap-2 text-text">
            <span>🛡️</span> {title}
          </h3>
          <p className="text-xs text-text-dim">
            Verified cryptographic defences in place for this execution.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {triggeredCount > 0 && (
            <span className="badge bg-rose-500/20 text-rose-400 font-bold border border-rose-500/40">
              🚨 {triggeredCount} Attack Caught
            </span>
          )}
          <span className="badge bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/40">
            🛡️ {activeCount}/{items.length} Defences Active
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {items.map((item, idx) => {
          const cfg = STATUS_CONFIG[item.status] || STATUS_CONFIG.not_in_mode;

          return (
            <motion.div
              key={item.id || idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className={`p-3.5 rounded-xl border flex flex-col justify-between transition-all ${cfg.cardBorder}`}
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-xs text-text flex items-center gap-1.5">
                    <span>{cfg.icon}</span> {item.name}
                  </span>
                  <span className={`badge border text-[10px] font-bold ${cfg.badgeClass}`}>
                    {cfg.label}
                  </span>
                </div>

                <div className="text-[11px] text-text-dim">
                  <strong className="text-text">Stops:</strong> {item.stops}
                </div>
              </div>

              {item.evidence && (
                <div className="mt-3 pt-2 border-t border-border/40 text-[11px] font-mono text-text/80 bg-surface-2/40 p-2 rounded">
                  <span className="text-text-dim">Evidence:</span> {item.evidence}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
