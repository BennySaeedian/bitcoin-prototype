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

    def get_potential_forked_chain_len(self, main_hash_chain: list[BlockHash]) -> int:
        """
        determines the potential length of the blockchain if all blocks in a new branch
        are valid and successfully appended to the current main blockchain.
        This method is employed to assess whether it's worthwhile to attempt validating a new
        branch and if it has the potential to surpass the current main blockchain.
        notice, this function assumes main_hash_chain has the genesis hash as the
        first block hash
        """
        common_hashes_len = main_hash_chain.index(self.fork_block_hash) + 1
        return common_hashes_len + len(self.new_branch)
