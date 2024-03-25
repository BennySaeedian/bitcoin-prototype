from hashlib import sha256

from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    PrivateFormat,
    NoEncryption
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from custom_typing import PrivateKey, Signature, PublicKey


def sign(message: bytes, private_key: PrivateKey) -> Signature:
    """signs the given message using the given private key"""
    private_key_object = Ed25519PrivateKey.from_private_bytes(
        private_key
    )
    return Signature(private_key_object.sign(message))


def verify(message: bytes, signature: Signature, public_key: PublicKey) -> bool:
    """
    verifies a signature for a given message using a public key
    returns true iff the signature matches
    """
    candidate = Ed25519PublicKey.from_public_bytes(data=public_key)
    try:
        candidate.verify(signature=signature, data=message)
        return True
    except:
        return False


def generate_keys() -> tuple[PrivateKey, PublicKey]:
    """
    generates a private key and a and its corresponding public key
    the keys are returned in bytes format to allow them to be serialized easily
    """
    private_key = Ed25519PrivateKey.generate()
    private_key_bytes = private_key.private_bytes(
        encoding=Encoding.Raw,
        format=PrivateFormat.Raw,
        encryption_algorithm=NoEncryption(),
    )
    public_key_bytes = private_key.public_key().public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )
    return PrivateKey(private_key_bytes), PublicKey(public_key_bytes)


def crypto_hash(input: bytes) -> bytes:
    """
    uses SHA256 to cryptographically hash inputs
    """
    return sha256(input).digest()
