import sys
import os
import importlib.metadata

# ANSI escape codes for coloring
GREEN = "\033[92m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

PACKAGES = [
    "numpy",
    "cryptography",
    ("kyber-py", "kyber_py"),
    "streamlit",
    "plotly",
    "pandas",
    "matplotlib",
    "rich",
    "pytest",
]

def print_banner():
    print("=" * 60)
    print("  HYBRID-QKD-PQC ENVIRONMENT VERIFICATION")
    print("=" * 60)
    print(f"Python Version: {sys.version.split()[0]} ({sys.executable})")

def verify_packages():
    print("\n[1/5] Checking installed package versions...")
    versions = {}
    for pkg in PACKAGES:
        if isinstance(pkg, tuple):
            name, alt = pkg
            try:
                ver = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                try:
                    ver = importlib.metadata.version(alt)
                except importlib.metadata.PackageNotFoundError:
                    raise RuntimeError(f"Package '{name}' is not installed.")
            versions[name] = ver
        else:
            try:
                ver = importlib.metadata.version(pkg)
                versions[pkg] = ver
            except importlib.metadata.PackageNotFoundError:
                raise RuntimeError(f"Package '{pkg}' is not installed.")
        print(f"  - {pkg if isinstance(pkg, str) else pkg[0]}: {versions[pkg if isinstance(pkg, str) else pkg[0]]}")
    return versions

def verify_kyber():
    print("\n[2/5] Testing ML-KEM-768 round trip (kyber-py)...")
    from kyber_py.ml_kem import ML_KEM_768
    ek, dk = ML_KEM_768.keygen()
    shared_a, ct = ML_KEM_768.encaps(ek)
    shared_b = ML_KEM_768.decaps(dk, ct)
    assert shared_a == shared_b, "ML-KEM-768 shared secrets do not match!"
    print(f"  OK: ML-KEM-768 keygen -> encaps -> decaps matched ({len(shared_a)} bytes shared secret).")

def verify_cryptography():
    print("\n[3/5] Testing HKDF-SHA256 and AES-256-GCM round trip...")
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    # HKDF-SHA256
    salt = os.urandom(16)
    info = b"hybrid-qkd-pqc-verification"
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=info,
    )
    derived_key = hkdf.derive(b"test-entropy-secret-seed")
    assert len(derived_key) == 32, "Derived key length must be 32 bytes for AES-256"

    # AES-256-GCM
    aesgcm = AESGCM(derived_key)
    nonce = os.urandom(12)
    plaintext = b"Quantum-safe encrypted channel test payload 123456"
    aad = b"authenticated-metadata"
    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
    decrypted = aesgcm.decrypt(nonce, ciphertext, aad)
    assert decrypted == plaintext, "AES-256-GCM decrypted plaintext does not match original!"
    print("  OK: HKDF-SHA256 derived 256-bit key and AES-256-GCM encrypt/decrypt verified.")

def verify_numpy():
    print("\n[4/5] Testing NumPy random bits and packbits/unpackbits round trip...")
    import numpy as np

    rng = np.random.default_rng(12345)
    bits = rng.integers(0, 2, size=128, dtype=np.uint8)
    packed = np.packbits(bits)
    unpacked = np.unpackbits(packed)[:128]
    assert np.array_equal(bits, unpacked), "NumPy packbits/unpackbits round trip failed!"
    print(f"  OK: NumPy bit manipulation verified on {len(bits)} bits.")

def verify_imports():
    print("\n[5/5] Testing imports for dashboard and visualization libraries...")
    import streamlit
    import plotly
    import pandas
    import matplotlib
    import rich
    print("  OK: streamlit, plotly, pandas, matplotlib, rich imported successfully.")

def main():
    try:
        # Enable ANSI colors on Windows console if available
        os.system("")
        print_banner()
        verify_packages()
        verify_kyber()
        verify_cryptography()
        verify_numpy()
        verify_imports()
        print("\n" + "=" * 60)
        print(f"{GREEN}{BOLD}ENVIRONMENT OK{RESET}")
        print("=" * 60)
        sys.exit(0)
    except Exception as exc:
        print("\n" + "=" * 60)
        print(f"{RED}{BOLD}VERIFICATION FAILED: {exc}{RESET}")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
