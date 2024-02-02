from custom_typing import BlockHash


class Constants:
    """
    simple namespace which stores the constants used in project
    """
    # every block is required to have a prev hash
    # this is the unique hash the every genesis block will have
    GENESIS_BLOCK_PREV = BlockHash(b"Genesis")
    # The maximal amount of transactions a block can include
    BLOCK_SIZE = 10
    # Number of coinbase transactions per block
    NUM_OF_COINBASE_PER_BLOCK = 1
    # SHA256 digest len in bytes
    SHA256_DIGEST_LEN = 256 // 8
