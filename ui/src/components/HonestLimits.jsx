export default function HonestLimits() {
  return (
    <footer className="mt-12 border-t border-border bg-surface/50 text-xs text-text-dim py-4 px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3 text-center md:text-left">
        <div className="flex items-center gap-2">
          <span className="text-sm">⚠️</span>
          <span className="font-semibold text-text">Honest Engineering Limitations:</span>
        </div>
        <p className="flex-1 max-w-4xl text-text-dim">
          BB84 is a software simulation • <code className="font-mono text-pqc">kyber-py</code> is educational and not constant-time • 
          BB84 assumes an authenticated classical channel, which this local demo does not provide.
        </p>
        <span className="badge bg-surface-3 text-text-dim border border-border">v2.0 Hybrid QSC</span>
      </div>
    </footer>
  );
}
