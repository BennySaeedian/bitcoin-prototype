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
