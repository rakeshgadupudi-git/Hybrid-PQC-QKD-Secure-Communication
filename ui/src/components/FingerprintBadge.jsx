export default function FingerprintBadge({ value, label }) {
  if (!value) return null;
  return (
    <span className="fingerprint-badge group relative" title="Fingerprint only: the real key never leaves the backend.">
      🔑 {label && <span className="text-text-dim mr-1">{label}:</span>}
      <span className="font-mono">{value}</span>
      <span className="absolute -top-8 left-1/2 -translate-x-1/2 bg-surface-2 text-xs text-text-dim px-2 py-1 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
        Fingerprint only — the real key never leaves the backend
      </span>
    </span>
  );
}
