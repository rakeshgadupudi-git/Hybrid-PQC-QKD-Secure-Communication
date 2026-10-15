export const STEP_DESCRIPTIONS = {
  hello: {
    title: 'Hello — session parameters',
    simple: 'Alice and Bob agree on which security mode to use and how many qubits to exchange. This is like shaking hands before starting a secure conversation.',
    technical: 'The initiator proposes the handshake mode (hybrid, pqc, qkd, or classical), the number of BB84 qubits, the ML-KEM security level, and channel parameters. Both sides must agree before proceeding.',
  },
  bb84_prepare: {
    title: 'Alice prepares qubits',
    simple: 'Alice creates thousands of tiny quantum particles (qubits), each randomly set to 0 or 1 in one of two random orientations (bases). These are the building blocks of a key that only she and Bob will share.',
    technical: 'Alice generates n random bits and n random bases (rectilinear {|0⟩,|1⟩} or diagonal {|+⟩,|−⟩}) using a CSPRNG. Each qubit encodes one bit in its assigned basis, producing a QubitBatch for transmission.',
  },
  bb84_transmit: {
    title: 'Qubits travel through the quantum channel',
    simple: 'Alice sends her qubits to Bob over the quantum channel. If an eavesdropper (Eve) tries to peek at them, she will inevitably disturb them — this disturbance is detectable later.',
    technical: 'The QubitBatch is transmitted through a simulated quantum channel. If Eve is active, she performs an intercept-resend attack: measuring each intercepted qubit in a random basis and re-preparing it. Channel noise adds independent bit-flip errors with probability p.',
  },
  bb84_measure: {
    title: 'Bob measures the qubits',
    simple: 'Bob receives the qubits and measures each one in a randomly chosen orientation. When his orientation matches Alice\'s, he gets the correct bit. When it doesn\'t, his result is random — like trying to read a message through the wrong filter.',
    technical: 'Bob chooses random measurement bases independently of Alice. For each qubit where his basis matches Alice\'s preparation basis, the measurement is deterministic. Mismatched bases produce a uniformly random outcome.',
  },
  bb84_sift: {
    title: 'Sifting — keep only matching bases',
    simple: 'Alice and Bob publicly compare which orientation they used for each qubit (but not the bit values). They keep only the bits where they used the same orientation — roughly half the total. These form the "sifted key".',
    technical: 'Alice and Bob exchange their basis arrays over an authenticated classical channel. Positions where alice_bases[i] == bob_bases[i] are kept; the rest are discarded. The expected sifted fraction is ≈ 50%.',
  },
  bb84_qber: {
    title: 'Checking for eavesdroppers (QBER)',
    simple: 'Alice and Bob sacrifice a fraction of their sifted bits to check for errors. If someone listened in, about a quarter of the compared bits will disagree. If the error rate is above 11%, they abort — someone is listening!',
    technical: 'A random 25% sample of the sifted key is compared publicly. The Quantum Bit Error Rate (QBER) is computed as errors/sample_size. Theory predicts QBER ≈ 25% × eve_rate for intercept-resend. The abort threshold is 11% (standard BB84). Sampled bits are discarded from the key.',
  },
  bb84_error_correction: {
    title: 'Error correction (Cascade)',
    simple: 'Alice and Bob fix the remaining errors in their shared bits using a clever technique: they compare parity (odd/even counts) of blocks, narrowing down where errors are, without revealing the actual bit values.',
    technical: 'Simplified Cascade protocol: multiple passes with increasing block sizes and random permutations. Each pass performs binary-search parity checks to locate and correct single-bit errors per block. Parity bits leaked are tracked for privacy amplification.',
  },
  bb84_privacy_amp: {
    title: 'Privacy amplification',
    simple: 'To ensure Eve has zero knowledge of the final key, Alice and Bob compress their bits through a mathematical "funnel" — throwing away any information that might have leaked. The output is a shorter but perfectly secret key.',
    technical: 'Toeplitz-matrix universal hashing over GF(2). Output length = input_bits − leaked_bits − security_margin. A public random seed defines the Toeplitz matrix. This guarantees the final key is ε-close to uniform even if Eve holds partial information.',
  },
  mlkem_keygen: {
    title: 'ML-KEM key generation',
    simple: 'Bob generates a special pair of keys designed to be safe against future quantum computers. The public key is sent to Alice; the private key stays secret with Bob.',
    technical: 'ML-KEM (FIPS 203) key generation at the configured security level (512/768/1024). Produces an encapsulation key (ek, public) and a decapsulation key (dk, private). Based on the Module-LWE problem.',
  },
  mlkem_encaps: {
    title: 'Alice encapsulates a shared secret',
    simple: 'Alice uses Bob\'s public key to create a shared secret and lock it in a "quantum-safe capsule" (ciphertext). Only Bob\'s private key can open it — even a future quantum computer cannot crack it.',
    technical: 'ML-KEM encapsulation: given Bob\'s ek, produces a 32-byte shared secret and a ciphertext. The ciphertext is sent to Bob. Security relies on the hardness of Module-LWE, believed to be resistant to Shor\'s algorithm.',
  },
  mlkem_decaps: {
    title: 'Bob decapsulates the shared secret',
    simple: 'Bob uses his private key to open the capsule and recover the same shared secret Alice created. If the capsule was tampered with, he gets a different (wrong) secret, and the protocol detects the mismatch.',
    technical: 'ML-KEM decapsulation: using dk and the received ciphertext, Bob recovers the shared secret. An implicit rejection mechanism returns a pseudorandom value if the ciphertext is invalid, preventing chosen-ciphertext attacks.',
  },
  hkdf_combine: {
    title: 'Hybrid key combination (HKDF)',
    simple: 'The QKD key and the PQC key are mixed together using a cryptographic blender (HKDF). The result is a single session key that stays secure even if one of the two components is broken in the future.',
    technical: 'HKDF-SHA256 combines length-prefixed QKD and PQC secrets (and optionally a classical secret) with the transcript hash as salt and a fixed info string. This ensures the session key is secure as long as at least one component remains uncompromised.',
  },
  key_confirm: {
    title: 'Key confirmation (HMAC)',
    simple: 'Alice and Bob each compute a "fingerprint" of their session key and exchange them. If the fingerprints match, they know for certain they ended up with the same key.',
    technical: 'Both parties compute HMAC-SHA256 over role-specific labels and the transcript hash, keyed with the session key. Comparing the HMAC tags confirms both sides derived identical keys and that the transcript was not tampered with.',
  },
  secure_chat: {
    title: 'Secure chat (AES-256-GCM)',
    simple: 'Alice sends Bob an encrypted message. The encryption (AES-256-GCM) ensures nobody can read or modify the message in transit. A built-in counter prevents old messages from being replayed.',
    technical: 'AES-256-GCM authenticated encryption with per-direction 96-bit nonces (4-byte direction prefix + 8-byte counter). The sequence number is included as AAD, detecting replays and reordering. A self-test verifies roundtrip, tamper rejection, and replay rejection.',
  },
};
