from typing import NewType

# throughout the project, we utilize a significant amount of bytes in various contexts
# to enhance code readability we define different types for these bytes
PrivateKey = NewType(name='PrivateKey', tp=bytes)

PublicKey = NewType(name='PublicKey', tp=bytes)

Signature = NewType(name='Signature', tp=bytes)

BlockHash = NewType(name='BlockHash', tp=bytes)

TransactionID = NewType(name="TransactionID", tp=bytes)

__all__ = [
    "PrivateKey",
    "PublicKey",
    "Signature",
    "BlockHash",
    "TransactionID",
]
