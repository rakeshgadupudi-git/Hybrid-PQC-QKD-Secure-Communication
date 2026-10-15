import useRunStore from '../store/useRunStore';

const MODES = [
  { value: 'hybrid', label: '🔐 Hybrid (QKD + PQC)', desc: 'Best protection: quantum + post-quantum' },
  { value: 'pqc', label: '🛡️ PQC only (ML-KEM)', desc: 'Post-quantum key exchange only' },
  { value: 'qkd', label: '🔑 QKD only (BB84)', desc: 'Quantum key distribution only' },
  { value: 'classical', label: '🔓 Classical (X25519)', desc: 'Traditional key exchange' },
];

export default function SetupPanel() {
  const {
    mode, setMode, eveOn, setEveOn, eveRate, setEveRate,
    noise, setNoise, qubits, setQubits, message, setMessage,
    run, loading,
  } = useRunStore();

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-4">⚙️ Setup</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Mode */}
        <div>
          <label className="label">Mode</label>
          <select className="input w-full mt-1" value={mode} onChange={(e) => setMode(e.target.value)}>
            {MODES.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
          <p className="text-xs text-text-dim mt-1">{MODES.find((m) => m.value === mode)?.desc}</p>
        </div>

        {/* Eve */}
        <div>
          <label className="label">Eavesdropper (Eve)</label>
          <div className="flex items-center gap-2 mt-1">
            <button
              className={`btn text-xs ${eveOn ? 'bg-eve text-white' : 'bg-surface-2 text-text-dim border border-border'}`}
              onClick={() => setEveOn(!eveOn)}
            >
              {eveOn ? '🕵️ Eve ON' : '🚫 Eve OFF'}
            </button>
          </div>
          {eveOn && (
            <div className="mt-2">
              <input
                type="range" min="0.05" max="1" step="0.05"
                value={eveRate} onChange={(e) => setEveRate(parseFloat(e.target.value))}
                className="w-full accent-eve"
              />
              <span className="text-xs text-eve font-mono">{(eveRate * 100).toFixed(0)}% intercept</span>
            </div>
          )}
        </div>

        {/* Qubits & Noise */}
        <div>
          <label className="label">Qubits</label>
          <select className="input w-full mt-1" value={qubits} onChange={(e) => setQubits(parseInt(e.target.value))}>
            {[512, 1024, 2048, 4096, 8192].map((n) => (
              <option key={n} value={n}>{n.toLocaleString()}</option>
            ))}
          </select>
          <label className="label mt-2 block">Noise</label>
          <input
            type="range" min="0" max="0.05" step="0.005"
            value={noise} onChange={(e) => setNoise(parseFloat(e.target.value))}
            className="w-full accent-alice mt-1"
          />
          <span className="text-xs text-text-dim font-mono">{(noise * 100).toFixed(1)}%</span>
        </div>

        {/* Message */}
        <div>
          <label className="label">Message</label>
          <textarea
            className="input w-full mt-1 h-20 resize-none"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Alice's message to Bob..."
          />
        </div>
      </div>

      <button
        className="btn-primary mt-4 w-full text-lg"
        onClick={run}
        disabled={loading}
      >
        {loading ? '⏳ Running...' : '▶️ Run Handshake'}
      </button>
    </div>
  );
}
