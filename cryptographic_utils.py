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
    pk = Ed25519PrivateKey.from_private_bytes(
        private_key
    )
    return Signature(pk.sign(message))


def verify(message: bytes, signature: Signature, public_key: PublicKey) -> bool:
    """
    verifies a signature for a given message using a public key
    returns true iff the signature matches
    """
    pub_k = Ed25519PublicKey.from_public_bytes(data=public_key)
    try:
        pub_k.verify(signature=signature, data=message)
        return True
    except:
        return False


def gen_keys() -> tuple[PrivateKey, PublicKey]:
    """
    generates a private key and a and its corresponding public key
    The keys are returned in bytes format to allow them to be serialized easily
    """
    private_key = Ed25519PrivateKey.generate()
    priv_key_bytes = private_key.private_bytes(
        encoding=Encoding.Raw,
        format=PrivateFormat.Raw,
        encryption_algorithm=NoEncryption(),
    )
    pub_key_bytes = private_key.public_key().public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )
    return PrivateKey(priv_key_bytes), PublicKey(pub_key_bytes)
