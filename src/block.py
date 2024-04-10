from cryptographic_utils import crypto_hash
from custom_typing import BlockHash
from transaction import Transaction


class Block:
    """
    this class represents a single block in the blockchain
    """

    def __init__(
            self,
            prev_block_hash: BlockHash,
            transactions: list[Transaction],
    ) -> None:
        self.prev_block_hash: BlockHash = prev_block_hash
        self.transactions: list[Transaction] = transactions

    def get_hash(self) -> BlockHash:
        """
        calculates and returns the hash of this block
        the hash depends on the contents of the block, that is
        the attached transactions and the previous block pointer
        """
        # concat all the transaction identifiers
        tx_ids: bytes = b''.join(tx.get_id() for tx in self.transactions)
        # also, concat the previous block hash
        block_identifier: bytes = tx_ids + self.prev_block_hash
        # hash the block using cryptographic hash function
        block_hash: bytes = crypto_hash(block_identifier)
        # convert to BlockHash which is subtype of bytes
        return BlockHash(block_hash)

    def get_transactions(self) -> list[Transaction]:
        """
        returns the list of transactions in this block.
        """
        return self.transactions

    def get_prev_block_hash(self) -> BlockHash:
        """Gets the hash of the previous block"""
        return self.prev_block_hash
    