import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { fetchBenchmarks } from '../api/client';

export default function Benchmarks() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchBenchmarks();
        setData(res);
      } catch (err) {
        setError(err.message || 'Benchmarks data not found. Please run: python benchmarks/run_benchmarks.py');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Format latency data (in milliseconds)
  const latencyChartData = data
    ? [
        {
          name: 'X25519',
          type: 'Classical',
          latencyMs: Number(((data.x25519?.mean || 0) * 1000).toFixed(2)),
          color: '#9ca3af',
        },
        {
          name: 'RSA-2048',
          type: 'Classical',
          latencyMs: Number(((data.rsa2048?.mean || 0) * 1000).toFixed(2)),
          color: '#ef4444',
        },
        {
          name: 'ML-KEM-512',
          type: 'PQC',
          latencyMs: Number((
            ((data.mlkem512?.keygen?.mean || 0) +
              (data.mlkem512?.encaps?.mean || 0) +
              (data.mlkem512?.decaps?.mean || 0)) *
            1000
          ).toFixed(2)),
          color: '#f97316',
        },
        {
          name: 'ML-KEM-768',
          type: 'PQC (NIST Rec)',
          latencyMs: Number((
            ((data.mlkem768?.keygen?.mean || 0) +
              (data.mlkem768?.encaps?.mean || 0) +
              (data.mlkem768?.decaps?.mean || 0)) *
            1000
          ).toFixed(2)),
          color: '#f97316',
        },
        {
          name: 'ML-KEM-1024',
          type: 'PQC',
          latencyMs: Number((
            ((data.mlkem1024?.keygen?.mean || 0) +
              (data.mlkem1024?.encaps?.mean || 0) +
              (data.mlkem1024?.decaps?.mean || 0)) *
            1000
          ).toFixed(2)),
          color: '#f97316',
        },
      ]
    : [];

  // Format key and ciphertext size data (in Bytes)
  const sizeChartData = data
    ? [
        {
          name: 'X25519',
          pkBytes: data.x25519?.key_size || 32,
          ctBytes: data.x25519?.ciphertext_size || 32,
        },
        {
          name: 'RSA-2048',
          pkBytes: data.rsa2048?.key_size || 294,
          ctBytes: data.rsa2048?.ciphertext_size || 256,
        },
        {
          name: 'ML-KEM-512',
          pkBytes: data.mlkem512?.ek_size || 800,
          ctBytes: data.mlkem512?.ct_size || 768,
        },
        {
          name: 'ML-KEM-768',
          pkBytes: data.mlkem768?.ek_size || 1184,
          ctBytes: data.mlkem768?.ct_size || 1088,
        },
        {
          name: 'ML-KEM-1024',
          pkBytes: data.mlkem1024?.ek_size || 1568,
          ctBytes: data.mlkem1024?.ct_size || 1568,
        },
      ]
    : [];

  // Format BB84 runtime data
  const bb84ChartData = data?.bb84_runtime
    ? Object.entries(data.bb84_runtime).map(([qubits, obj]) => ({
        qubits: `${qubits} qubits`,
        runtimeMs: Number(((obj?.mean || 0) * 1000).toFixed(2)),
      }))
    : [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2 text-text">
          <span>⏱️</span> Empirical Performance & Cryptographic Benchmarks
        </h2>
        <p className="text-sm text-text-dim mt-1">
          Measured benchmarks comparing classical, post-quantum (ML-KEM), and quantum key distribution execution times and footprint.
        </p>
      </div>

      {error && (
        <div className="card border-amber-500/50 bg-amber-500/10 text-amber-300 text-sm space-y-2">
          <div className="flex items-center gap-2 font-bold">
            <span>⚠️</span> Benchmark Data Notice
          </div>
          <p>{error}</p>
          <p className="text-xs text-text-dim font-mono">
            Execute in your shell: <code>python benchmarks/run_benchmarks.py</code>
          </p>
        </div>
      )}

      {loading && (
        <div className="p-8 text-center text-text-dim text-sm">
          Loading benchmark metrics...
        </div>
      )}

      {data && (
        <div className="space-y-8">
          {/* Top highlight stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="card p-4 space-y-1">
              <span className="text-xs text-text-dim uppercase font-bold tracking-wider">Fastest KEX</span>
              <div className="text-xl font-bold font-mono text-alice">X25519 (ECDH)</div>
              <div className="text-xs text-text-dim">
                ~{((data.x25519?.mean || 0) * 1000).toFixed(2)} ms (Not Quantum-Safe)
              </div>
            </div>

            <div className="card p-4 space-y-1 border-pqc/40">
              <span className="text-xs text-text-dim uppercase font-bold tracking-wider">Standard PQC</span>
              <div className="text-xl font-bold font-mono text-pqc">ML-KEM-768</div>
              <div className="text-xs text-text-dim">
                NIST FIPS 203 Level 3 (AES-192 Equivalent)
              </div>
            </div>

            <div className="card p-4 space-y-1 border-hybrid/40">
              <span className="text-xs text-text-dim uppercase font-bold tracking-wider">BB84 Simulation (4K)</span>
              <div className="text-xl font-bold font-mono text-hybrid">
                ~{((data.bb84_runtime?.['4096']?.mean || 0) * 1000).toFixed(2)} ms
              </div>
              <div className="text-xs text-text-dim">
                Full session: prepare, sift, EC, & privacy amp
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart 1: Latency */}
            <div className="card space-y-3">
              <h3 className="text-base font-bold text-text flex items-center gap-2">
                <span>⚡</span> Full Key Exchange Latency (ms)
              </h3>
              <p className="text-xs text-text-dim">
                Combined generation, encapsulation, and decapsulation roundtrip time.
              </p>
              <div className="h-72 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={latencyChartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.5} />
                    <XAxis dataKey="name" stroke="#9ca3af" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#9ca3af" unit=" ms" tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e1e2e', borderColor: '#3f3f5c', borderRadius: '8px' }}
                      formatter={(val) => [`${val} ms`, 'Roundtrip Latency']}
                    />
                    <Bar dataKey="latencyMs" name="Roundtrip Latency (ms)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Public Key & Ciphertext Sizes */}
            <div className="card space-y-3">
              <h3 className="text-base font-bold text-text flex items-center gap-2">
                <span>📦</span> Key & Ciphertext Overhead (Bytes)
              </h3>
              <p className="text-xs text-text-dim">
                Wire footprint comparison: Public Key (ek) vs. Ciphertext (ct).
              </p>
              <div className="h-72 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={sizeChartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.5} />
                    <XAxis dataKey="name" stroke="#9ca3af" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#9ca3af" unit=" B" tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e1e2e', borderColor: '#3f3f5c', borderRadius: '8px' }}
                      formatter={(val, name) => [`${val} Bytes`, name === 'pkBytes' ? 'Public Key' : 'Ciphertext']}
                    />
                    <Legend verticalAlign="top" height={36} />
                    <Bar dataKey="pkBytes" name="Public Key (Bytes)" fill="#f97316" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="ctBytes" name="Ciphertext (Bytes)" fill="#a855f7" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Chart 3: BB84 Runtime Scaling */}
          {bb84ChartData.length > 0 && (
            <div className="card space-y-3">
              <h3 className="text-base font-bold text-text flex items-center gap-2">
                <span>⚛️</span> BB84 Protocol Simulation Scaling
              </h3>
              <p className="text-xs text-text-dim">
                Wall-clock time for end-to-end BB84 distillation across increasing raw photon counts.
              </p>
              <div className="h-64 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={bb84ChartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.5} />
                    <XAxis dataKey="qubits" stroke="#9ca3af" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#9ca3af" unit=" ms" tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e1e2e', borderColor: '#3f3f5c', borderRadius: '8px' }}
                      formatter={(val) => [`${val} ms`, 'Execution Time']}
                    />
                    <Bar dataKey="runtimeMs" name="BB84 Total Time (ms)" fill="#eab308" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
