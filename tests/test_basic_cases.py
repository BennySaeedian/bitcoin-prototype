import pytest

from src import *


def test_node_at_init(alice: Node) -> None:
    assert alice.get_address()
    assert alice.get_utxo() == []
    assert alice.get_mempool() == []
    assert alice.get_balance() == 0
    assert alice.get_latest_hash() == Constants.GENESIS_BLOCK_PREV
    alice_public_key = alice.get_address()
    assert alice.create_transaction(alice_public_key) is None


def test_block_mining(alice: Node) -> None:
    block_hash = alice.mine_block()
    assert block_hash != Constants.GENESIS_BLOCK_PREV
    assert alice.get_latest_hash() == block_hash
    assert alice.get_balance() == 1
    assert len(alice.get_utxo()) == 1
    assert alice.get_mempool() == []
    block = alice.get_block(block_hash)
    assert block.get_hash() == block_hash
    assert block.get_prev_block_hash() == Constants.GENESIS_BLOCK_PREV
    transactions = block.get_transactions()
    assert len(transactions) == 1
    transaction, *_ = transactions
    assert transaction == alice.get_utxo()[0]
    assert transaction.is_coinbase
    assert transaction.output == alice.get_address()
    
    
def test_block_retrieval(alice: Node) -> None:
    with pytest.raises(ValueError):
        alice.get_block(Constants.GENESIS_BLOCK_PREV)
    junk_hash = BlockHash(b'beneath this mask there is an idea and ideas are bulletproof')
    with pytest.raises(ValueError):
        alice.get_block(junk_hash)
    actual_block_hash = alice.mine_block()
    with pytest.raises(ValueError):
        alice.get_block(junk_hash)
    assert type(alice.get_block(actual_block_hash)) == Block