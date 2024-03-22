from __future__ import annotations

from constants import Constants
from custom_typing import TransactionID, PublicKey, BlockHash
from cryptographic_utils import generate_keys
from data_classes import ForkData, NodeState
from transaction import Transaction
from block import Block
from validations import validate_transaction_pre_mempool_access, validate_block_structure


class Node:
    """represents a participator in a de-centralized economy"""

    def __init__(self) -> None:
        """
        creates a new node with a public address and empty state
        """
        self._private_key, self._public_key = generate_keys()
        self._state = NodeState()
        self._connections: set[Node] = set()
        # efficiency related data-structures:
        self._id_to_transaction: dict[TransactionID, Transaction] = dict()

    def connect(self, other: Node) -> None:
        """
        establishes a bi-directional connection between nodes for block and transaction
        updates, preventing connection to itself, without immediate mempool updates
        but ensuring instant block notifications
        """
        if other.get_address() == self._public_key:
            raise ValueError("Can not connect a node to itself")
        # if the two nodes are already connected, bounce
        if other in self._connections:
            return
        # else, do bi-directional connection between the two
        self._connections.add(other)
        other.connect(other=self)
        # notify the other node, other node will notify upon his connect
        other.get_introduced_to_new_block(
            block_hash=self.get_latest_hash(),
            sender=self,
        )

    def disconnect_from(self, other: Node) -> None:
        """
        disconnects this node from the other node and vise versa, idempotent
        """
        # bounce if there is no connection
        if other not in self._connections:
            return
        # else, there is a connection, disconnect both
        self._connections.remove(other)
        other.disconnect_from(other=self)

    def get_address(self) -> PublicKey:
        """
        returns the address of the node, the public key
        """
        return self._public_key

    def get_connections(self) -> set[Node]:
        """
        returns a set containing the connections of this node.
        """
        return self._connections

    def get_mempool(self) -> list[Transaction]:
        """
        this function returns the list of transactions that didn't
        enter any block yet.
        """
        return self._state.mempool

    def get_latest_hash(self) -> BlockHash:
        """
        this function returns the last block hash known to this node,
        the tip of its current chain.
        """
        return (
            self._state.blockchain[-1].get_hash() if self._state.blockchain
            else Constants.GENESIS_BLOCK_PREV
        )

    def get_block(self, block_hash: BlockHash) -> Block:
        """
        this function returns a block object given its hash.
        if the block doesn't exist a ValueError is raised.
        """
        for block in self._state.blockchain:
            if block.get_hash() == block_hash:
                return block
        # If the block doesn't exist, a ValueError is raised.
        raise ValueError("Block does not exist in node's blockchain")

    def add_transaction_to_mempool(self, transaction: Transaction) -> bool:
        """
        this function adds the provided transaction to the mempool,
        returning false if the transaction is invalid,
        the source lacks the necessary funds, or if there's a conflicting transaction
        in the mempool. valid transactions are propagated to neighboring nodes.
        """
        is_valid_transaction: bool = validate_transaction_pre_mempool_access(
            transaction=transaction,
            state=self._state,
            id_to_transaction=self._id_to_transaction,
        )
        if not is_valid_transaction:
            return False
        # else, can enter the mempool
        self._add_new_transaction_to_mempool(transaction)
        # notify the others
        self._publish_new_transaction(transaction=transaction)
        return True

    def get_introduced_to_new_block(
            self,
            block_hash: BlockHash,
            sender: Node
    ) -> None:
        """
        handles the reception of new blocks by a node's connection,
        requesting unknown blocks and processing received blocks for validity.
        if the received block is on the longest chain, it triggers adjustments to the
        mempool and utxo, and notifies neighboring nodes.
        possible blockchain reorganizations are managed by rolling back the utxo to the
        split point and updating along the new branch, with caution for potentially
        invalid blocks. conflicting transactions are removed from the mempool during
        this process.
        """
        curr_hash_chain = self._get_blockchain_hashes()
        # if we know this block no need to do anything
        if block_hash in curr_hash_chain:
            return
        # else, we need to find the forking point, it can be the tip of the
        # current chain or in the middle of it
        try:
            fork_data: ForkData = self._find_forking_point(
                block_hash=block_hash,
                sender=sender,
            )
        except ValueError:
            return
        # check if this new branch has the potential to beat the current
        # main chain given the new branch is valid
        potential_new_chain_len = fork_data.get_potential_forked_chain_len(
            main_hash_chain=curr_hash_chain
        )
        if potential_new_chain_len <= len(curr_hash_chain):
            return
        # now validate the new branch and get the updated state
        new_state = self._reorg_blockchain(fork_data)
        # if the new branch surpasses the current one in terms of size, adopt it
        if len(self._state.blockchain) < len(new_state.blockchain):
            self._state = new_state
            # notify the others
            self._publish_latest_block()

    def _add_new_transaction_to_mempool(self, transaction: Transaction) -> None:
        """
        updates internal state upon new transaction arrival in the mempool
        """
        # add it to the mempool list
        self._state.mempool.append(transaction)
        # map it to its txid for efficient retrival
        self._id_to_transaction[transaction.get_id()] = transaction

    def _publish_new_transaction(self, transaction: Transaction) -> None:
        """
        notify other node connections of new mempool transactions, idempotent.
        """
        transaction_id = transaction.get_id()
        for node in self._connections:
            connection_known_txs = [tx.get_id() for tx in node.get_mempool()]
            if transaction_id not in connection_known_txs:
                node.add_transaction_to_mempool(transaction=transaction)

    def _get_blockchain_hashes(self) -> list[BlockHash]:
        """
        returns the ordered list of the current state's blockchain hashes
        """
        return (
                [Constants.GENESIS_BLOCK_PREV]
                + [b.get_hash() for b in self._state.blockchain]
        )

    def _find_forking_point(
            self,
            block_hash: BlockHash,
            sender: Node,
    ) -> ForkData:
        """
        iterates until it find the forking point of the given block_hash
        and the current's node blockchain
        """
        new_branch, new_branch_hashes = [], []
        # iterate until we find the forking point
        running_hash = block_hash
        while running_hash not in self._get_blockchain_hashes():
            running_block = sender.get_block(running_hash)
            # add the new branch and its hash to the start of the list
            # so at the end we will have the branch sorted
            new_branch = [running_block] + new_branch
            new_branch_hashes = [running_hash] + new_branch_hashes
            running_hash = running_block.get_prev_block_hash()

        return ForkData(
            fork_block_hash=running_hash,
            new_branch=new_branch,
            new_branch_hashes=new_branch_hashes,
        )

    def _reorg_blockchain(self, fork_data: ForkData) -> NodeState:
        """
        reverts the state to the forking point, adds the new valid blocks and updates
        the state
        """
        state = self._state.copy()
        # first we need to revert to the blockchain to the forking point
        self._rollback_state_to_forking_point(
            fork_hash=fork_data.fork_block_hash,
            state=state
        )
        # when we reach here, all the blocks which should have been reverted
        # are rolled-back and saved in the temporary state we are maintaining
        # now, we need to add new blocks to the tip and validate them
        self._add_new_branch_to_state(
            branch=fork_data.new_branch,
            branch_hashes=fork_data.new_branch_hashes,
            state=state
        )
        return state

    def _rollback_latest_block(
            self,
            state: NodeState,
    ) -> Block:
        """
        rolls back the latest block the given state and returns it
        """
        latest_block = state.blockchain.pop()
        block_transactions = latest_block.get_transactions()
        block_transaction_ids = [t.get_id() for t in block_transactions]
        # remember every transaction can be seen as a coin, or as a transaction
        # output that the receiver can spend. but if we revert this block
        # we need to deny the given coin to every receiver who gained the coin
        # via this block

        state.utxo = [t for t in state.utxo if t not in block_transactions]
        # now, let's add back the inputs that were spent in this block
        # excluding coinbase transactions
        curr_block_spent_transactions: list[Transaction] = [
            self._id_to_transaction[t.input] for t in block_transactions
            if not t.is_coinbase
        ]
        state.utxo += curr_block_spent_transactions
        # additionally, we need to remove transactions in the mempool
        # which try to spend coins which were introduced in the latest block
        state.mempool = [
            t for t in state.mempool if t.input not in block_transaction_ids
        ]
        return latest_block

    def _rollback_state_to_forking_point(
            self,
            fork_hash: BlockHash,
            state: NodeState,
    ) -> None:
        """
        rolls back the state to the provided fork-hash
        notice that if the provided hash is the tip of the current blockchain
        this function has no effect since no re-rolls are needed
        """
        current_hash = self.get_latest_hash()
        while current_hash != fork_hash:
            rolled_back_block = self._rollback_latest_block(state)
            current_hash = rolled_back_block.get_prev_block_hash()

    def _add_new_branch_to_state(
            self,
            branch: list[Block],
            branch_hashes: list[BlockHash],
            state: NodeState,
    ) -> None:
        """
        in charge of adding a new branch, which consists of multiple successive blocks,
        to the provided state
        """
        for block, block_hash in zip(branch, branch_hashes):
            is_valid_block = self._validate_block_and_update_state(
                block=block,
                block_hash=block_hash,
                state=state,
            )
            # if we encounter an invalid block in the branch we trim the branch
            if not is_valid_block:
                return

    def _validate_block_and_update_state(
            self,
            block: Block,
            block_hash: BlockHash,
            state: NodeState,
    ) -> bool:
        """
        In charge of validating a block and update the given state
        """
        has_valid_structure = validate_block_structure(
            block=block,
            block_hash=block_hash
        )
        if not has_valid_structure:
            return False
        # while validating the transaction we will use a temp state
        # this is because we want to update the given state only once every transaction
        # passed the validation test
        temp_state = state.copy()
        for transaction in block.get_transactions():
            # no need to validate coinbase transactions
            if not transaction.is_coinbase:
                is_valid_transaction = validate_transaction_pre_mempool_access(
                    transaction=transaction,
                    state=temp_state,
                    id_to_transaction=self._id_to_transaction
                )
                # if any of the transactions is invalid, the whole block is invalid
                if not is_valid_transaction:
                    return False
            # if we got here the transaction is valid
            self._introduce_valid_transaction_into_state(
                transaction=transaction,
                state=temp_state
            )
        # if we got here the whole block is valid
        state.utxo = temp_state.utxo
        state.mempool = temp_state.mempool
        state.blockchain = state.blockchain + [block]

    def _introduce_valid_transaction_into_state(
            self,
            transaction: Transaction,
            state: NodeState,
    ) -> None:
        """
        Updates state internals upon new valid transaction
        """
        transaction_id = transaction.get_id()
        # Once a transaction entered the blockchain, it can be removed from the mempool
        # also, any other transaction which tries to spend this transaction
        # input is invalid, so let's remove it
        state.mempool = [
            t for t in state.mempool
            if t != transaction and t.input != transaction.input
        ]
        # every valid transaction spends an input unless it is a coinbase tx
        # lets remove this input from the utxo
        if not transaction.is_coinbase:
            state.utxo = [t for t in state.utxo if t.get_id() != transaction.input]
        # every valid transaction introduces new inputs which can be spent
        state.utxo.append(transaction)
        # lastly, extend the txid to tx mapping
        self._id_to_transaction[transaction_id] = transaction

    def _publish_latest_block(self):
        """
        informs all other connections that a new block has been introduced
        """
        for connection in self._connections:
            connection.get_introduced_to_new_block(
                block_hash=self.get_latest_hash(),
                sender=self
            )
