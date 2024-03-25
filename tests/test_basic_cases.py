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
    assert alice.get_balance() == Constants.NUM_OF_COINBASE_PER_BLOCK
    assert len(alice.get_utxo()) == Constants.NUM_OF_COINBASE_PER_BLOCK
    assert alice.get_mempool() == []
    block = alice.get_block(block_hash)
    assert block.get_hash() == block_hash
    assert block.get_prev_block_hash() == Constants.GENESIS_BLOCK_PREV
    transactions = block.get_transactions()
    assert len(transactions) == Constants.NUM_OF_COINBASE_PER_BLOCK
    transaction, *_ = transactions
    assert transaction.get_id() == alice.get_utxo()[0].get_id()
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
    assert alice.get_block(actual_block_hash)


def test_connections(alice: Node, bob: Node, charlie: Node) -> None:
    alice.connect(bob)
    first_hash = alice.mine_block()
    assert {bob.get_latest_hash(), alice.get_latest_hash()} == {first_hash}
    assert charlie.get_latest_hash() == Constants.GENESIS_BLOCK_PREV
    second_hash = bob.mine_block()
    assert {bob.get_latest_hash(), alice.get_latest_hash()} == {second_hash}
    charlies_hash = charlie.mine_block()
    assert charlie.get_latest_hash() == charlies_hash
    assert {bob.get_latest_hash(), alice.get_latest_hash()} == {second_hash}


def test_moving_funds_and_balances(alice: Node, bob: Node) -> None:
    alice.mine_block()
    assert alice.get_balance() == Constants.NUM_OF_COINBASE_PER_BLOCK
    transaction = alice.create_transaction(bob.get_address())
    assert transaction
    assert transaction.input == alice.get_utxo()[0].get_id()
    assert transaction.output == bob.get_address()
    assert transaction in alice.get_mempool()
    assert bob.get_balance() == 0
    bob.connect(alice)
    assert bob.get_balance() == 0
    bob.mine_block()
    assert bob.get_balance() == Constants.NUM_OF_COINBASE_PER_BLOCK
    assert bob.get_mempool() == []
    alice.mine_block()
    assert alice.get_mempool() == []
    assert alice.get_balance() == Constants.NUM_OF_COINBASE_PER_BLOCK
    assert bob.get_balance() == Constants.NUM_OF_COINBASE_PER_BLOCK + 1


def test_reorgs(alice: Node, bob: Node, charlie: Node) -> None:
    pass