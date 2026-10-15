import { motion } from 'framer-motion';

export default function KeyFunnel({ funnel }) {
  if (!funnel) return null;

  const rawStages = [
    { label: 'Raw qubits', value: funnel.raw, color: '#3b82f6' },
    { label: 'Sifted', value: funnel.sifted, color: '#8b5cf6' },
    { label: 'After sample', value: funnel.after_sample, color: '#a855f7' },
    { label: 'After EC', value: funnel.after_ec, color: '#d946ef' },
    { label: 'Final key', value: funnel.final_bits, color: '#eab308' },
  ];

  const stages = rawStages.filter((s) => s.value != null);
  const maxVal = Math.max(...stages.map((s) => Number(s.value) || 0), 1);

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-text-dim">Key Distillation Funnel</h4>
      {stages.map((s, i) => {
        const val = Number(s.value) || 0;
        return (
          <div key={s.label} className="flex items-center gap-2">
            <span className="text-xs text-text-dim w-24 text-right">{s.label}</span>
            <div className="flex-1 relative h-5 bg-surface-3 rounded overflow-hidden">
              <motion.div
                className="h-full rounded"
                style={{ backgroundColor: s.color }}
                initial={{ width: 0 }}
                animate={{ width: `${(val / maxVal) * 100}%` }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
              />
            </div>
            <span className="text-xs font-mono w-16 text-right">{val.toLocaleString()}</span>
          </div>
        );
      })}
    </div>
  );
}
