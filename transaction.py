from typing import Optional

from cryptographic_utils import crypto_hash
from custom_typing import PublicKey, TxID, Signature


class Transaction:
    """
    represents a transaction that moves a single coin
    a coin base transaction is a transaction which has no source / input
    and basically creates money
    """

    def __init__(
            self,
            output: PublicKey,
            tx_input: Optional[TxID],
            signature: Signature
    ) -> None:
        # the node which receives the coin
        self.output: PublicKey = output
        # the coin being spent (can be None for coinbase txs)
        self.input: Optional[TxID] = tx_input
        # signature created with a private key of the payer
        # the message is the payee and the coin being spent (output + input)
        # other nodes will verify that indeed the payer signed the tx
        self.signature: Signature = signature

    def get_id(self) -> TxID:
        """
        returns the identifier of this transaction.
        that is the sha256 digest of the transaction contents
        """
        # concat all the fields which identify a single transaction
        tx_identifier: bytes = (
                self.output
                + (self.input or b'')  # input can be None
                + self.signature
        )
        # hash the identifier using sha256
        tx_hash: bytes = crypto_hash(tx_identifier)
        # convert to TxID which is subtype of bytes
        return TxID(tx_hash)

    @property
    def is_coinbase(self) -> bool:
        """
        returns true iff this is a coinbase transaction which creates money
        """
        return self.input is None
