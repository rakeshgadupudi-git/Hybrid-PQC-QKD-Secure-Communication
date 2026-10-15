/**
 * API client for the hybrid QKD-PQC backend.
 */

const API_BASE = 'http://127.0.0.1:8000';
const WS_BASE = 'ws://127.0.0.1:8000';

export async function fetchHealth() {
  const r = await fetch(`${API_BASE}/api/health`);
  return r.json();
}

export async function fetchSteps() {
  const r = await fetch(`${API_BASE}/api/steps`);
  return r.json();
}

export async function fetchCompare() {
  const r = await fetch(`${API_BASE}/api/compare`);
  return r.json();
}

export async function fetchBenchmarks() {
  const r = await fetch(`${API_BASE}/api/benchmarks`);
  if (!r.ok) {
    const err = await r.json();
    throw new Error(err.hint || err.error || 'Benchmarks not found');
  }
  return r.json();
}

export async function fetchSweep(qubits = 4000, trials = 5, noise = 0) {
  const r = await fetch(`${API_BASE}/api/bb84/sweep?qubits=${qubits}&trials=${trials}&noise=${noise}`);
  return r.json();
}

export async function postBb84Lab(params) {
  const r = await fetch(`${API_BASE}/api/bb84/lab`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return r.json();
}

export async function postRunPair(params) {
  const r = await fetch(`${API_BASE}/api/run/pair`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return r.json();
}

export async function postChatStart(params) {
  const r = await fetch(`${API_BASE}/api/chat/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return r.json();
}

export async function postChatSend(params) {
  const r = await fetch(`${API_BASE}/api/chat/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return r.json();
}

export async function postAttackEve(params) {
  const r = await fetch(`${API_BASE}/api/attack/eve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return r.json();
}

export async function postAttackTamper(params) {
  const r = await fetch(`${API_BASE}/api/attack/tamper`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return r.json();
}

export async function postAttackReplay(params) {
  const r = await fetch(`${API_BASE}/api/attack/replay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return r.json();
}

/**
 * Open a WebSocket to run a handshake.
 * Returns a promise that resolves with all events.
 */
export function runHandshakeWs(params) {
  return new Promise((resolve, reject) => {
    const qs = new URLSearchParams({
      mode: params.mode || 'hybrid',
      eve_rate: String(params.eve_rate ?? 0),
      noise: String(params.noise ?? 0),
      qubits: String(params.qubits ?? 2048),
      message: params.message || 'Hello Bob, this is Alice.',
    });
    const ws = new WebSocket(`${WS_BASE}/ws/run?${qs}`);
    const events = [];

    ws.onmessage = (e) => {
      try {
        events.push(JSON.parse(e.data));
      } catch (err) {
        console.error('Failed to parse WS message:', err);
      }
    };
    ws.onerror = (e) => reject(e);
    ws.onclose = () => resolve(events);
  });
}
