from __future__ import annotations

from constants import Constants
from custom_typing import TxID, PublicKey, BlockHash
from cryptographic_utils import sign, verify, gen_keys
from data_classes import ForkData, NodeState
from transaction import Transaction
from block import Block
from validations import validate_transaction_pre_mempool_access, validate_block_structure


class Node:
    """
    a node which participates in a de-centralized economy
    """

    def __init__(self) -> None:
        """
        creates a new node with an empty mempool and no connections to others.
        blocks mined by this node will reward the miner with a single new coin,
        created out of thin air and associated with the mining reward address.
        each node manages its own mempool, and
        its own copy of the blockchain and UTxO set.
        we can think of a node as the combination of a de-centralized bank
        and a crypto-wallet
        """
        self._private_key, self._public_key = gen_keys()
        self._state = NodeState()
        self._connections: set[Node] = set()
        # efficiency related data-structures:
        self._txid_to_tx: dict[TxID, Transaction] = dict()

    def connect(self, other: Node) -> None:
        """
        connects this node to another node for block and transaction updates.
        connections are bi-directional,
        so the other node is connected to this one as well.
        raises an exception if asked to connect to itself.
        The connection itself does not trigger updates about the mempool,
        but nodes instantly notify of their latest block to each other
        """
        if other.get_address() == self._public_key:
            raise Exception("Can not connect a node to itself")
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
        disconnects this node from the other node
        if the two were not connected, then nothing happens
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
        this function inserts the given transaction to the mempool.
        it will return False iff any of the following conditions hold:
        (i) the transaction is invalid (the signature fails)
        (ii) the source doesn't have the coin that it tries to spend
        (iii) there is contradicting tx in the mempool.
        if the transaction is added successfully,
        then it is also sent to neighboring nodes.
        transactions that create money (with no inputs)
        are not placed in the mempool, and not propagated.
        """
        is_valid_transaction = validate_transaction_pre_mempool_access(
            transaction=transaction,
            utxo=self._state.utxo,
            mempool=self._state.mempool,
            txid_to_tx=self._txid_to_tx,
        )
        if not is_valid_transaction:
            return False
        # else, can enter the mempool
        self._add_new_tx_to_mempool(transaction)
        # notify the others
        self._publish_new_transaction(transaction=transaction)
        return True

    def get_introduced_to_new_block(
            self,
            block_hash: BlockHash,
            sender: Node
    ) -> None:
        """
        this method is used by a node's connection to inform it that it has
        learned of a new block or created a new one
        if the block is unknown to the current Node, The block is requested.
        we assume the sender of the message is specified, so that the node can
        choose to request this block if it wishes to do so.
        (if it is part of a longer unknown chain, these blocks are requested
        as well, until reaching a known block).
        upon receiving new blocks, they are processed and checked for validity
        (check all signatures, hashes, block size , etc.).
        if the block is on the longest chain, the mempool and utxo
        change accordingly. ties, i.e., chains of similar length to that of
        this node are not adopted.
        if the block is indeed the tip of the longest chain,
        a notification of this block is sent to the neighboring nodes of
        this node. no need to notify of previous blocks -- the nodes will
        fetch them if needed.
        a reorg may be triggered by this block's introduction.
        In this case the utxo is rolled back to the split point,
        and then rolled forward along the new branch.
        Be careful - the new branch may contain invalid blocks.
        these and blocks that point to them should not be accepted to
        the blockchain but earlier valid blocks may still form a longer chain
        the mempool is similarly emptied of transactions that cannot
        be executed now.
        transactions that were rolled back and can still be executed are
        re-introduced into the mempool if they do not conflict.
        """
        curr_hash_chain = self._get_blockchain_hashes()
        # if we know this block no need to do anything
        if block_hash in curr_hash_chain:
            return
        # else, we need to find the forking point, it can be the tip of the
        # current chain or in the middle of it
        try:
            fork_data = self._find_forking_point(
                block_hash=block_hash,
                sender=sender,
            )
        except ValueError:
            return
        new_branch_potential_len = (
            # the len which is similar to the current blockchain
                curr_hash_chain.index(fork_data.fork_block_hash) + 1
                + len(fork_data.new_branch)  # with the len of the new branch
        )
        # this check is before validating the blocks
        # if this new branch is not longer no need to check it
        if new_branch_potential_len <= len(curr_hash_chain):
            return

    def _add_new_tx_to_mempool(self, transaction: Transaction) -> None:
        """
        This method should be called upon every new tx that enters
        the mempool. This method is in charge of updating all the inner
        data structures
        """
        # add it to the mempool list
        self._state.mempool.append(transaction)
        # map it to its txid for efficient retrival
        self._txid_to_tx[transaction.get_id()] = transaction

    def _publish_new_transaction(self, transaction: Transaction) -> None:
        """
        idempotent method which notifies the connections of the node that
        a new transaction has been added to the mempool, should be called
        upon the introduction of every new transaction
        """
        transaction_id = transaction.get_id()
        for node in self._connections:
            connection_known_txs = [tx.get_id() for tx in node.get_mempool()]
            if transaction_id not in connection_known_txs:
                node.add_transaction_to_mempool(transaction=transaction)

    def _get_blockchain_hashes(self) -> list[BlockHash]:
        """
        returns the ordered list of the current blockchain hashes
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
        rolls back the latest block the given state, returns the new state
        and the rolled-back block
        """
        latest_block = state.blockchain.pop()
        block_transactions = latest_block.get_transactions()
        block_transaction_ids = [t.get_id() for t in block_transactions]
        # remember the given block is the tip of the current
        # blockchain, which means every output there is unspent
        # and hence must be in the utxo
        # if we roll back this block we need to remove them from the given utxo
        state.utxo = [t for t in state.utxo if t not in block_transactions]
        # now, let's add back the inputs that were spent in this block
        # excluding coinbase transactions
        curr_block_spent_transactions: list[Transaction] = [
            self._txid_to_tx[t.input] for t in block_transactions
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
        this function has no effect since no rerolls are needed
        """
        current_hash = self.get_latest_hash()
        while current_hash != fork_hash:
            state, rolled_back_block = self._rollback_latest_block(state)
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
            if not is_valid_block:
                return

    def _validate_block_and_update_state(
            self,
            block: Block,
            block_hash: BlockHash,
            state: NodeState,
    ) -> bool:
        """
        TODO
        """
        has_valid_structure = validate_block_structure(
            block=block,
            block_hash=block_hash
        )
        if not has_valid_structure:
            return False

        

