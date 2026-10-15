import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { postBb84Lab, fetchSweep } from '../api/client';
import QberGauge from '../components/QberGauge';
import KeyFunnel from '../components/KeyFunnel';
import FingerprintBadge from '../components/FingerprintBadge';

export default function Bb84Lab() {
  // Single Simulation State
  const [qubits, setQubits] = useState(4096);
  const [eveRate, setEveRate] = useState(0.0);
  const [noise, setNoise] = useState(0.0);
  const [labResult, setLabResult] = useState(null);
  const [labLoading, setLabLoading] = useState(false);

  // Sweep State
  const [sweepData, setSweepData] = useState([]);
  const [sweepLoading, setSweepLoading] = useState(false);
  const [sweepTrials, setSweepTrials] = useState(3);

  const runSimulation = async () => {
    setLabLoading(true);
    try {
      const res = await postBb84Lab({
        qubits,
        eve_rate: eveRate,
        noise,
      });
      setLabResult(res);
    } catch (err) {
      console.error('BB84 lab failed:', err);
    } finally {
      setLabLoading(false);
    }
  };

  const runSweep = async () => {
    setSweepLoading(true);
    try {
      const records = await fetchSweep(qubits, sweepTrials, noise);
      // Format records for Recharts
      const chartPoints = records.map((r) => ({
        ratePct: Math.round(r.rate * 100),
        measuredQberPct: Number((r.qber_mean * 100).toFixed(2)),
        theoreticalPct: Number((0.25 * r.rate * 100).toFixed(2)),
        thresholdPct: 11.0,
      }));
      setSweepData(chartPoints);
    } catch (err) {
      console.error('Sweep failed:', err);
    } finally {
      setSweepLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
    runSweep();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2 text-text">
          <span>🔬</span> BB84 Quantum Key Distribution Laboratory
        </h2>
        <p className="text-sm text-text-dim mt-1">
          Interactive simulator and parameter sweep for the Bennett-Brassard 1984 protocol, evaluating quantum bit error rates against photon interception.
        </p>
      </div>

      {/* Part 1: Interactive Single Run Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls Column */}
        <div className="card space-y-4">
          <h3 className="text-base font-bold text-text flex items-center gap-2">
            <span>🎛️</span> Channel & Quantum Parameters
          </h3>

          <div className="space-y-4 text-xs">
            {/* Qubits */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-text-dim">Raw Qubits (n):</span>
                <span className="font-mono font-bold text-text">{qubits.toLocaleString()}</span>
              </div>
              <input
                type="range"
                min="512"
                max="8192"
                step="512"
                value={qubits}
                onChange={(e) => setQubits(parseInt(e.target.value))}
                className="w-full accent-alice"
              />
            </div>

            {/* Eve Rate */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-text-dim">Eve Intercept Rate:</span>
                <span className="font-mono font-bold text-eve">{Math.round(eveRate * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={eveRate}
                onChange={(e) => setEveRate(parseFloat(e.target.value))}
                className="w-full accent-eve"
              />
            </div>

            {/* Noise */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-text-dim">Optical Channel Noise:</span>
                <span className="font-mono font-bold text-amber-400">{(noise * 100).toFixed(1)}%</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="0.05"
                step="0.005"
                value={noise}
                onChange={(e) => setNoise(parseFloat(e.target.value))}
                className="w-full accent-amber-400"
              />
            </div>

            <button
              onClick={runSimulation}
              disabled={labLoading}
              className="btn-primary w-full text-xs font-bold pt-2.5 pb-2.5"
            >
              {labLoading ? 'Simulating Quantum Channel...' : '▶ Run BB84 Simulation'}
            </button>
          </div>
        </div>

        {/* Results Column (Span 2) */}
        <div className="card lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h3 className="text-base font-bold text-text flex items-center gap-2">
              <span>📊</span> Simulation Output & Key Distillation
            </h3>
            {labResult && (
              <span
                className={`badge font-bold text-xs ${
                  labResult.accepted
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                }`}
              >
                {labResult.accepted ? '✅ KEY ESTABLISHED' : '🚨 ABORTED (QBER HIGH)'}
              </span>
            )}
          </div>

          {labResult && (
            <div className="space-y-5">
              {/* Gauges & Funnel Row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                <div className="flex flex-col items-center p-3 bg-surface-2 rounded-xl border border-border">
                  <QberGauge qber={labResult.qber} threshold={0.11} />
                  <div className="text-xs font-mono mt-1 text-text-dim">
                    Threshold: 11.0% | Eve Intercepted: {labResult.eve_intercepted}
                  </div>
                </div>

                <div className="p-3 bg-surface-2 rounded-xl border border-border space-y-2">
                  <span className="text-xs font-bold text-text-dim uppercase tracking-wider">
                    Distillation Funnel
                  </span>
                  <KeyFunnel funnel={labResult.funnel} />
                  {labResult.final_key_fingerprint && (
                    <div className="pt-2 border-t border-border flex items-center justify-between text-xs">
                      <span className="font-semibold text-qkd">256-bit Key Fingerprint:</span>
                      <FingerprintBadge value={labResult.final_key_fingerprint} label="QKD" />
                    </div>
                  )}
                </div>
              </div>

              {/* Step Timings Breakdown */}
              {labResult.timings && (
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-text-dim">
                    Stage Execution Latencies (ms)
                  </span>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 text-center text-xs">
                    {Object.entries(labResult.timings).map(([stage, ms]) => (
                      <div key={stage} className="p-2 bg-surface-2 rounded border border-border">
                        <div className="text-[10px] text-text-dim capitalize">{stage}</div>
                        <div className="font-mono font-bold text-text">{ms} ms</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Part 2: QBER Sweep Chart */}
      <div className="card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-3">
          <div>
            <h3 className="text-lg font-bold flex items-center gap-2 text-text">
              <span>📈</span> QBER vs. Intercept Rate (Empirical vs. Theoretical Line)
            </h3>
            <p className="text-xs text-text-dim">
              The theoretical intercept-resend attack introduces a linear error: <code className="text-pqc font-mono">QBER = 0.25 × EveRate</code>.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-text-dim">
              <span>Trials/Point:</span>
              <select
                value={sweepTrials}
                onChange={(e) => setSweepTrials(parseInt(e.target.value))}
                className="input py-1 text-xs"
              >
                <option value={1}>1 (Fast)</option>
                <option value={3}>3 (Balanced)</option>
                <option value={5}>5 (High Precision)</option>
              </select>
            </div>

            <button
              onClick={runSweep}
              disabled={sweepLoading}
              className="btn-secondary text-xs flex items-center gap-1.5"
            >
              <span>🔄</span> {sweepLoading ? 'Sweeping...' : 'Re-calculate Sweep'}
            </button>
          </div>
        </div>

        {/* Recharts LineChart */}
        <div className="h-80 w-full pt-4">
          {sweepData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sweepData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.5} />
                <XAxis
                  dataKey="ratePct"
                  stroke="#9ca3af"
                  unit="%"
                  label={{ value: 'Eve Intercept Rate (%)', position: 'insideBottom', offset: -10, fill: '#9ca3af' }}
                />
                <YAxis
                  stroke="#9ca3af"
                  unit="%"
                  domain={[0, 30]}
                  label={{ value: 'QBER (%)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e1e2e', borderColor: '#3f3f5c', borderRadius: '8px' }}
                  labelFormatter={(v) => `Eve Intercept: ${v}%`}
                  formatter={(val, name) => [`${val}%`, name]}
                />
                <Legend verticalAlign="top" height={36} />
                <ReferenceLine
                  y={11}
                  stroke="#ef4444"
                  strokeDasharray="4 4"
                  label={{ value: '11% Abort Threshold', fill: '#ef4444', position: 'right' }}
                />
                <Line
                  type="monotone"
                  dataKey="measuredQberPct"
                  name="Empirical QBER (Simulated)"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#3b82f6' }}
                />
                <Line
                  type="monotone"
                  dataKey="theoreticalPct"
                  name="Theory (0.25 × Rate)"
                  stroke="#a855f7"
                  strokeDasharray="5 5"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-full text-xs text-text-dim">
              {sweepLoading ? 'Generating sweep points...' : 'No sweep data available.'}
            </div>
          )}
        </div>

        <div className="text-xs text-text-dim bg-surface-2/40 p-3 rounded-lg border border-border leading-relaxed">
          💡 <strong>Physical Proof:</strong> In BB84, Alice sends photons polarized randomly in Rectilinear (+) or Diagonal (×) bases. Eve cannot clone the photons (No-Cloning Theorem). When Eve measures in the wrong basis (50% probability) and re-prepares, Bob will have a 50% chance of getting the wrong bit upon measuring in Alice's basis. Hence, <code className="font-mono text-alice">0.50 × 0.50 = 0.25</code> error rate for every intercepted qubit. At ~44% interception, the error crosses 11%, where classical error-correction leakage exceeds remaining entropy.
        </div>
      </div>
    </div>
  );
}
