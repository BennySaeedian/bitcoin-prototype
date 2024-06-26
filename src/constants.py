from custom_typing import BlockHash

# every block is required to have a prev hash
# this is the unique hash that every genesis block will have
GENESIS_BLOCK_PREV = BlockHash(b"Genesis")
# The maximal amount of transactions a block can include
BLOCK_SIZE = 10
# Number of coinbase transactions per block
NUM_OF_COINBASE_PER_BLOCK = 1
# Number of allowed mempool transactions per block
NUM_OF_MEMPOOL_TXS_PER_BLOCK = BLOCK_SIZE - NUM_OF_COINBASE_PER_BLOCK
# SHA256 digest len in bytes
SHA256_DIGEST_LEN = 256 // 8
# cryptographic signature length in bytes
SIGNATURE_LEN = 64

__all__ = [
    "GENESIS_BLOCK_PREV",
    "BLOCK_SIZE",
    "NUM_OF_COINBASE_PER_BLOCK",
    "NUM_OF_MEMPOOL_TXS_PER_BLOCK",
    "SHA256_DIGEST_LEN",
    "SIGNATURE_LEN"
]
