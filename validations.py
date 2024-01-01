from block import Block
from constants import Constants
from cryptographic_utils import verify
from custom_typing import TxID, BlockHash
from transaction import Transaction


def validate_transaction_pre_mempool_access(
        transaction: Transaction,
        utxo: list[Transaction],
        mempool: list[Transaction],
        txid_to_tx: dict[TxID, Transaction],
) -> bool:
    """
    checks whether the specified coin in the transaction
    input indeed belongs to the payer and makes sure it is unspent
    makes sure there is no contradicting transaction which tires to spend the
    same input in the given mempool
    """
    # make sure it passes the sanity test of every input
    is_valid_type = (
            type(transaction.input) == bytes
            and len(transaction.input) == Constants.SHA256_DIGEST_LEN
    )
    if not is_valid_type:
        return False
    # the input field of each transaction specifies which
    # coin is being spent, get it
    coin_being_spent: Transaction = txid_to_tx.get(transaction.input)
    # if there is not such coin, invalid coin is being spent
    if coin_being_spent in None:
        return False
    # we also need to verify that the payer is the one who singed the tx
    coin_being_spent_owner = coin_being_spent.output
    does_signature_match: bool = verify(
        # the txid being spent concatenated with the target is the message
        message=transaction.input + transaction.output,
        # the signature should match the payer's PK
        signature=transaction.signature,
        # coin_being_spent.output is the owner of the coin being spent
        # since he is the one who got the coin
        public_key=coin_being_spent_owner

    )
    # if it failed tries to spend money he does not own
    if not does_signature_match:
        return False
    # we check that the coin is unspent in the given utxo set
    coin_is_unspent = transaction.input in [t.get_id() for t in utxo]
    if not coin_is_unspent:
        return False
    # finally, we make sure there is no other transaction which tires
    # to spend this coin in the mempool
    return transaction.input not in [tx.input for tx in mempool]


def validate_block_structure(
        block: Block,
        block_hash: BlockHash
) -> bool:
    """
    validates block properties, without validating every single attached
    transaction
    """
    transactions = block.get_transactions()
    coinbase_txs = [t for t in transactions if t.is_coinbase]

    return all(
        [
            # validate the calculated hash matches the one requested
            block.get_hash() == block_hash,
            # validate the size of a block
            len(transactions) <= Constants.BLOCK_SIZE,
            # validate number of coinbase transactions
            len(coinbase_txs) == Constants.NUM_OF_COINBASE_PER_BLOCK
        ]
    )
