/**
 * Design tokens and colour palette for the quantum-safe UI.
 */
const theme = {
  colors: {
    alice: { base: '#3b82f6', light: '#93c5fd', dark: '#1d4ed8', bg: 'rgba(59,130,246,0.1)' },
    bob: { base: '#22c55e', light: '#86efac', dark: '#15803d', bg: 'rgba(34,197,94,0.1)' },
    eve: { base: '#ef4444', light: '#fca5a5', dark: '#b91c1c', bg: 'rgba(239,68,68,0.1)' },
    qkd: { base: '#a855f7', light: '#d8b4fe', dark: '#7e22ce' },
    pqc: { base: '#f97316', light: '#fdba74', dark: '#c2410c' },
    hybrid: { base: '#eab308', light: '#fde047', dark: '#a16207' },
    success: '#22c55e',
    danger: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82f6',
  },
  statusIcon: {
    active: '🛡️',
    triggered: '🚨',
    not_in_mode: '➖',
    failed: '❌',
    not_reached: '⏭️',
  },
  statusColor: {
    active: '#22c55e',
    triggered: '#ef4444',
    not_in_mode: '#6b7280',
    failed: '#ef4444',
    not_reached: '#9ca3af',
  },
  actorLabel: {
    alice: '👩 Alice',
    bob: '👨 Bob',
    system: '⚙️ System',
  },
};

export default theme;
