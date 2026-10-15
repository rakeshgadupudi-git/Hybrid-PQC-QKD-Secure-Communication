export default function QubitTable({ data, type }) {
  const sample = data?.sample;
  if (!sample || sample.length === 0) return null;

  if (type === 'prepare') {
    return (
      <div className="overflow-x-auto">
        <table className="text-xs font-mono w-full">
          <thead>
            <tr className="text-text-dim">
              <th className="px-2 py-1 text-left">#</th>
              <th className="px-2 py-1">Bit</th>
              <th className="px-2 py-1">Basis</th>
            </tr>
          </thead>
          <tbody>
            {sample.map((q) => (
              <tr key={q.i} className="border-t border-border/30">
                <td className="px-2 py-0.5 text-text-dim">{q.i}</td>
                <td className="px-2 py-0.5 text-center">{q.bit}</td>
                <td className="px-2 py-0.5 text-center">{q.basis === 0 ? '➕' : '✖️'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (type === 'transmit') {
    return (
      <div className="overflow-x-auto">
        <table className="text-xs font-mono w-full">
          <thead>
            <tr className="text-text-dim">
              <th className="px-2 py-1 text-left">#</th>
              <th className="px-2 py-1">Intercepted</th>
              <th className="px-2 py-1">Flipped</th>
            </tr>
          </thead>
          <tbody>
            {sample.map((q) => (
              <tr key={q.i} className={`border-t border-border/30 ${q.intercepted ? 'bg-eve/5' : ''}`}>
                <td className="px-2 py-0.5 text-text-dim">{q.i}</td>
                <td className="px-2 py-0.5 text-center">
                  {q.intercepted ? <span className="text-eve">🕵️</span> : '—'}
                </td>
                <td className="px-2 py-0.5 text-center">
                  {q.flipped ? <span className="text-eve font-bold">⚡</span> : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (type === 'measure') {
    return (
      <div className="overflow-x-auto">
        <table className="text-xs font-mono w-full">
          <thead>
            <tr className="text-text-dim">
              <th className="px-2 py-1 text-left">#</th>
              <th className="px-2 py-1">Basis</th>
              <th className="px-2 py-1">Bit</th>
            </tr>
          </thead>
          <tbody>
            {sample.map((q) => (
              <tr key={q.i} className="border-t border-border/30">
                <td className="px-2 py-0.5 text-text-dim">{q.i}</td>
                <td className="px-2 py-0.5 text-center">{q.basis === 0 ? '➕' : '✖️'}</td>
                <td className="px-2 py-0.5 text-center">{q.bit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (type === 'sift') {
    return (
      <div className="overflow-x-auto">
        <div className="flex gap-1 flex-wrap">
          {sample.map((q) => (
            <span
              key={q.i}
              className="inline-block w-6 h-6 text-center text-xs font-mono rounded bg-bob/20 text-bob border border-bob/30"
              title={`Qubit ${q.i}: bases matched`}
            >
              ✓
            </span>
          ))}
        </div>
        <p className="text-xs text-text-dim mt-1">
          Kept {data.kept} of {data.total} qubits ({((data.kept / data.total) * 100).toFixed(1)}%)
        </p>
      </div>
    );
  }

  return null;
}
