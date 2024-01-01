from typing import NewType

# types to distinguish between private or public keys
# and cryptographic signatures
PrivateKey = NewType(name='PrivateKey', tp=bytes)
PublicKey = NewType(name='PublicKey', tp=bytes)
Signature = NewType(name='Signature', tp=bytes)

# we make similar type definitions for hashes:
# this will be the hash of a block
BlockHash = NewType(name='BlockHash', tp=bytes)
# this will be a hash of a transaction
TxID = NewType(name="TxID", tp=bytes)
