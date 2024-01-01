from __future__ import annotations

from dataclasses import dataclass, field
from copy import deepcopy
from block import Block
from custom_typing import BlockHash
from transaction import Transaction


@dataclass
class NodeState:
    """
    data structure used to store the internal state of a node
    """
    # committed blocks in the current states blockchain
    blockchain: list[Block] = field(default_factory=list)
    # unspent transaction outputs, coins which can be spent
    utxo: list[Transaction] = field(default_factory=list)
    # valid transactions which are waiting to be included in a block
    mempool: list[Transaction] = field(default_factory=list)

    def copy(self) -> NodeState:
        """
        returns a deep copy of this data-structure
        """
        return deepcopy(self)


@dataclass
class ForkData:
    """
    data structure is employed to store the necessary information
    whenever the blockchain experiences a fork with multiple branches
    """
    fork_block_hash: BlockHash
    new_branch: list[Block]
    new_branch_hashes: list[BlockHash]
