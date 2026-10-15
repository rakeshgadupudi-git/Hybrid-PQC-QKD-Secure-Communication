/**
 * Zustand store for handshake run state and playback.
 */
import { create } from 'zustand';
import { runHandshakeWs } from '../api/client';

const useRunStore = create((set, get) => ({
  // Parameters
  mode: 'hybrid',
  eveOn: false,
  eveRate: 0.0,
  noise: 0.0,
  qubits: 2048,
  message: 'Hello Bob, this is Alice.',

  // State
  events: [],
  plan: null,
  playbackIndex: -1,
  playing: false,
  speed: 1.0,
  presentationMode: false,
  loading: false,
  error: null,
  aborted: false,
  abortReason: '',

  // Setters
  setMode: (mode) => set({ mode }),
  setEveOn: (on) => set({ eveOn: on, eveRate: on ? 1.0 : 0.0 }),
  setEveRate: (rate) => set({ eveRate: rate }),
  setNoise: (noise) => set({ noise }),
  setQubits: (qubits) => set({ qubits }),
  setMessage: (message) => set({ message }),
  setSpeed: (speed) => set({ speed }),
  setPresentationMode: (on) => set({ presentationMode: on }),

  // Derived: step events only
  stepEvents: () => get().events.filter((e) => e.type === 'step'),
  scorecardEvent: () => get().events.find((e) => e.type === 'scorecard'),
  doneEvent: () => get().events.find((e) => e.type === 'done'),
  abortedEvent: () => get().events.find((e) => e.type === 'aborted'),

  // Current visible events (up to playback index)
  visibleSteps: () => {
    const steps = get().stepEvents();
    const idx = get().playbackIndex;
    if (idx < 0) return [];
    return steps.slice(0, idx + 1);
  },

  currentStep: () => {
    const steps = get().stepEvents();
    const idx = get().playbackIndex;
    if (idx < 0 || idx >= steps.length) return null;
    return steps[idx];
  },

  // Run
  run: async () => {
    const { mode, eveOn, eveRate, noise, qubits, message } = get();
    set({ loading: true, error: null, events: [], plan: null, playbackIndex: -1, playing: false, aborted: false, abortReason: '' });

    try {
      const events = await runHandshakeWs({
        mode,
        eve_rate: eveOn ? eveRate : 0.0,
        noise,
        qubits,
        message,
      });

      const plan = events.find((e) => e.type === 'plan');
      const abortedEv = events.find((e) => e.type === 'aborted');

      set({
        events,
        plan: plan?.data?.stages || null,
        loading: false,
        aborted: !!abortedEv,
        abortReason: abortedEv?.data?.reason || '',
        playbackIndex: 0,
      });
    } catch (err) {
      set({ loading: false, error: err.message || 'Connection failed' });
    }
  },

  // Playback controls
  next: () => {
    const steps = get().stepEvents();
    const idx = get().playbackIndex;
    if (idx < steps.length - 1) {
      set({ playbackIndex: idx + 1 });
    }
  },

  back: () => {
    const idx = get().playbackIndex;
    if (idx > 0) {
      set({ playbackIndex: idx - 1 });
    }
  },

  jumpTo: (idx) => {
    const steps = get().stepEvents();
    if (idx >= 0 && idx < steps.length) {
      set({ playbackIndex: idx });
    }
  },

  play: () => {
    set({ playing: true });
  },

  pause: () => {
    set({ playing: false });
  },

  togglePlay: () => {
    set((s) => ({ playing: !s.playing }));
  },

  reset: () => {
    set({
      events: [],
      plan: null,
      playbackIndex: -1,
      playing: false,
      aborted: false,
      abortReason: '',
      error: null,
    });
  },
}));

export default useRunStore;
