"""Classical key-exchange primitives: X25519 ECDH and RSA key transport.

Used for benchmark comparison against post-quantum alternatives.
"""

from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric import x25519, rsa, padding as asym_padding
from cryptography.hazmat.primitives import hashes, serialization


class X25519KeyExchange:
    """Ephemeral X25519 Diffie-Hellman key exchange.

    Each instance represents one party.  Call :meth:`generate` to
    create a keypair, exchange public keys, then call :meth:`derive`
    to compute the shared secret.
    """

    def __init__(self) -> None:
        self._private: x25519.X25519PrivateKey | None = None
        self._public: x25519.X25519PublicKey | None = None

    def generate(self) -> bytes:
        """Generate a new X25519 keypair and return the public key bytes.

        Returns:
            Raw 32-byte public key.
        """
        self._private = x25519.X25519PrivateKey.generate()
        self._public = self._private.public_key()
        return self._public.public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )

    def derive(self, peer_public_bytes: bytes) -> bytes:
        """Derive the shared secret from the peer's public key.

        Args:
            peer_public_bytes: The peer's raw 32-byte public key.

        Returns:
            32-byte shared secret.
        """
        assert self._private is not None, "Call generate() first"
        peer_pub = x25519.X25519PublicKey.from_public_bytes(peer_public_bytes)
        return self._private.exchange(peer_pub)


class RSAKeyTransport:
    """RSA-2048 OAEP key transport (for benchmark comparison only).

    One party generates an RSA keypair, the other encrypts a random
    secret with the public key, and the first party decrypts it.
    """

    def __init__(self) -> None:
        self._private: rsa.RSAPrivateKey | None = None
        self._public: rsa.RSAPublicKey | None = None

    def generate_keypair(self) -> bytes:
        """Generate an RSA-2048 keypair and return the public key (DER).

        Returns:
            DER-encoded public key bytes.
        """
        self._private = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self._public = self._private.public_key()
        return self._public.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def encrypt(self, public_key_der: bytes, plaintext: bytes) -> bytes:
        """Encrypt *plaintext* with the peer's RSA public key.

        Args:
            public_key_der: DER-encoded RSA public key.
            plaintext: Data to encrypt (max ~190 bytes for RSA-2048-OAEP-SHA256).

        Returns:
            Ciphertext bytes.
        """
        pub = serialization.load_der_public_key(public_key_der)
        assert isinstance(pub, rsa.RSAPublicKey)
        return pub.encrypt(
            plaintext,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt a ciphertext with our private key.

        Args:
            ciphertext: RSA-OAEP ciphertext.

        Returns:
            The original plaintext.
        """
        assert self._private is not None, "Call generate_keypair() first"
        return self._private.decrypt(
            ciphertext,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
