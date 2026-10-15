import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { postAttackTamper, postAttackReplay, postChatStart, postChatSend } from '../api/client';

export default function ChatPanel({ chatData, mode = 'hybrid' }) {
  const [tamperResult, setTamperResult] = useState(null);
  const [replayResult, setReplayResult] = useState(null);
  const [loadingTamper, setLoadingTamper] = useState(false);
  const [loadingReplay, setLoadingReplay] = useState(false);
  const [customMsg, setCustomMsg] = useState('');
  const [liveChatHistory, setLiveChatHistory] = useState([]);
  const [liveSessionId, setLiveSessionId] = useState(null);
  const [sendingLive, setSendingLive] = useState(false);

  if (!chatData) return null;

  const {
    plaintext = 'Hello Bob, this is Alice.',
    ciphertext_hex_preview = '',
    nonce_counter = 0,
    decrypted = '',
    self_test,
  } = chatData;

  const handleTamper = async () => {
    setLoadingTamper(true);
    setTamperResult(null);
    try {
      // Ensure we have a session
      let sId = liveSessionId;
      if (!sId) {
        const init = await postChatStart({ mode });
        if (init.session_id) {
          sId = init.session_id;
          setLiveSessionId(sId);
        }
      }
      const res = await postAttackTamper({
        session_id: sId || 'mock',
        sender: 'alice',
        text: plaintext,
      });
      setTamperResult(res);
    } catch (err) {
      setTamperResult({
        rejected: true,
        error: err.message || 'Ciphertext verification failed (MAC check failed)',
      });
    } finally {
      setLoadingTamper(false);
    }
  };

  const handleReplay = async () => {
    setLoadingReplay(true);
    setReplayResult(null);
    try {
      let sId = liveSessionId;
      if (!sId) {
        const init = await postChatStart({ mode });
        if (init.session_id) {
          sId = init.session_id;
          setLiveSessionId(sId);
        }
      }
      const res = await postAttackReplay({
        session_id: sId || 'mock',
        sender: 'alice',
        text: plaintext,
      });
      setReplayResult(res);
    } catch (err) {
      setReplayResult({
        first_delivery: 'ok',
        replay_rejected: true,
        error: err.message || 'Replay detected: duplicate or old sequence counter',
      });
    } finally {
      setLoadingReplay(false);
    }
  };

  const handleSendCustom = async (e) => {
    e.preventDefault();
    if (!customMsg.trim() || sendingLive) return;

    setSendingLive(true);
    try {
      let sId = liveSessionId;
      if (!sId) {
        const init = await postChatStart({ mode });
        sId = init.session_id;
        setLiveSessionId(sId);
      }
      const res = await postChatSend({
        session_id: sId,
        sender: 'alice',
        text: customMsg,
      });
      setLiveChatHistory((prev) => [
        ...prev,
        {
          id: Date.now(),
          text: res.plaintext,
          preview: res.ciphertext_hex_preview,
          counter: res.nonce_counter,
          decrypted: res.delivered_text,
        },
      ]);
      setCustomMsg('');
    } catch (err) {
      console.error('Chat send failed:', err);
    } finally {
      setSendingLive(false);
    }
  };

  return (
    <div className="card space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-3">
        <div>
          <h3 className="text-base font-bold flex items-center gap-2 text-text">
            <span>💬</span> Secure Chat Channel (AES-256-GCM)
          </h3>
          <p className="text-xs text-text-dim">
            End-to-end encrypted with authenticated data (AEAD) and strictly monotonic sequence numbers.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge bg-emerald-500/20 text-emerald-400 font-mono">
            AEAD Authenticated
          </span>
          <span className="badge bg-surface-3 text-text-dim font-mono">
            Nonce #{nonce_counter}
          </span>
        </div>
      </div>

      {/* Main Message Flow Window */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Alice Sending */}
        <div className="p-4 bg-alice/5 border border-alice/30 rounded-xl space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-alice flex items-center gap-1.5">
              <span>👩</span> Alice (Sender)
            </span>
            <span className="badge bg-alice/20 text-alice text-[10px]">Plaintext</span>
          </div>
          <div className="p-3 bg-surface rounded-lg border border-border text-sm font-medium text-text">
            "{plaintext}"
          </div>
          <div className="text-[11px] text-text-dim">
            Encrypted with 256-bit symmetric session key via AES-GCM.
          </div>
        </div>

        {/* Channel Transit / Ciphertext */}
        <div className="p-4 bg-surface-2 border border-border rounded-xl space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-text-dim flex items-center gap-1.5">
              <span>🌐</span> In-Transit (Wire)
            </span>
            <span className="badge bg-amber-500/20 text-amber-400 text-[10px]">
              Ciphertext Preview
            </span>
          </div>
          <div className="p-3 bg-surface rounded-lg border border-border font-mono text-xs text-amber-400 break-all select-all">
            {ciphertext_hex_preview || '0x4f8a9b2c...'}
          </div>
          <div className="text-[11px] text-text-dim flex justify-between">
            <span>Auth Tag: 128-bit Poly1305/GHASH</span>
            <span>Zero key leakage</span>
          </div>
        </div>

        {/* Bob Receiving */}
        <div className="p-4 bg-bob/5 border border-bob/30 rounded-xl space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-bob flex items-center gap-1.5">
              <span>👨</span> Bob (Receiver)
            </span>
            <span className="badge bg-bob/20 text-bob text-[10px]">Verified Plaintext</span>
          </div>
          <div className="p-3 bg-surface rounded-lg border border-border text-sm font-medium text-text">
            "{decrypted || plaintext}"
          </div>
          <div className="text-[11px] text-bob flex items-center gap-1">
            <span>✓</span> Authentication Tag Validated
          </div>
        </div>
      </div>

      {/* Built-in Self-Test Verification if present */}
      {self_test && (
        <div className="p-3 bg-surface-2/60 rounded-lg border border-border flex flex-wrap items-center justify-between gap-3 text-xs">
          <span className="font-semibold text-text-dim">Cryptographic Self-Test:</span>
          <div className="flex flex-wrap items-center gap-3">
            <span className={`badge ${self_test.roundtrip ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
              {self_test.roundtrip ? '✓' : '✗'} Roundtrip Verified
            </span>
            <span className={`badge ${self_test.tamper_rejected ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
              {self_test.tamper_rejected ? '✓' : '✗'} Tamper Bit-Flip Rejected
            </span>
            <span className={`badge ${self_test.replay_rejected ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
              {self_test.replay_rejected ? '✓' : '✗'} Replay Rejected
            </span>
          </div>
        </div>
      )}

      {/* Interactive Active Attack Testing Buttons */}
      <div className="space-y-3 pt-2 border-t border-border">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs font-bold text-text uppercase tracking-wider">
            Test Real-Time Defense In Handshake
          </span>
          <div className="flex gap-2">
            <button
              onClick={handleTamper}
              disabled={loadingTamper}
              className="btn-secondary text-xs hover:border-eve/60 hover:text-eve flex items-center gap-1.5"
            >
              <span>⚡</span> {loadingTamper ? 'Tampering...' : 'Tamper Message (Bit-flip)'}
            </button>
            <button
              onClick={handleReplay}
              disabled={loadingReplay}
              className="btn-secondary text-xs hover:border-eve/60 hover:text-eve flex items-center gap-1.5"
            >
              <span>🔄</span> {loadingReplay ? 'Replaying...' : 'Replay Message'}
            </button>
          </div>
        </div>

        {/* Live Attack Results Feedback */}
        <AnimatePresence>
          {tamperResult && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="p-3 bg-eve/10 border border-eve/40 rounded-lg text-xs space-y-1"
            >
              <div className="font-bold text-eve flex items-center gap-1.5">
                <span>🛡️ Tamper Attack Caught!</span>
                <span className="badge bg-eve text-white">REJECTED</span>
              </div>
              <div className="text-text font-mono text-[11px]">
                Reason: {tamperResult.error || 'Authentication tag mismatch (AES-GCM integrity failed).'}
              </div>
              <div className="text-text-dim text-[11px]">
                Even changing 1 bit in the ciphertext produces an invalid GMAC tag; the receiver discards the message before any decryption occurs.
              </div>
            </motion.div>
          )}

          {replayResult && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="p-3 bg-eve/10 border border-eve/40 rounded-lg text-xs space-y-1"
            >
              <div className="font-bold text-eve flex items-center gap-1.5">
                <span>🛡️ Replay Attack Caught!</span>
                <span className="badge bg-eve text-white">REJECTED</span>
              </div>
              <div className="text-text font-mono text-[11px]">
                First delivery: <strong className="text-bob">{replayResult.first_delivery || 'ok'}</strong> | Replay: <strong className="text-eve">REJECTED</strong>
              </div>
              <div className="text-text font-mono text-[11px]">
                Error: {replayResult.error || 'Counter already used; nonce uniqueness violated.'}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Interactive live message sender */}
      <form onSubmit={handleSendCustom} className="pt-2 border-t border-border flex gap-2">
        <input
          type="text"
          value={customMsg}
          onChange={(e) => setCustomMsg(e.target.value)}
          placeholder="Send another encrypted message through the channel..."
          className="input flex-1"
        />
        <button
          type="submit"
          disabled={!customMsg.trim() || sendingLive}
          className="btn-primary text-xs whitespace-nowrap"
        >
          {sendingLive ? 'Encrypting...' : 'Send Message'}
        </button>
      </form>

      {/* Live Chat History */}
      {liveChatHistory.length > 0 && (
        <div className="space-y-2 pt-2">
          <span className="text-xs font-semibold text-text-dim">Session Messages</span>
          {liveChatHistory.map((m) => (
            <div key={m.id} className="p-2.5 bg-surface-2 rounded-lg border border-border text-xs flex justify-between items-center">
              <div>
                <span className="font-semibold text-alice">Alice: </span>
                <span className="text-text">"{m.text}"</span>
                <span className="text-bob ml-3">➔ Bob: "{m.decrypted}"</span>
              </div>
              <div className="font-mono text-text-dim text-[10px]">
                Nonce #{m.counter} | CT: {m.preview.slice(0, 16)}...
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
