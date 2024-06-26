from typing import Optional

from src.cryptographic_utils import crypto_hash
from src.custom_typing import PublicKey, TransactionID, Signature


class Transaction:
    """
    represents a transaction that moves a single coin
    a coin base transaction is a transaction which has no source / input
    and basically creates money
    """

    def __init__(
            self,
            output: PublicKey,
            input: Optional[TransactionID],
            signature: Signature
    ) -> None:
        # the node which receives the coin
        self.output: PublicKey = output
        # the transaction being spent (can be None for coinbase txs)
        self.input: Optional[TransactionID] = input
        # signature created with a private key of the payer
        # the message is the payee and the coin being spent (output + input)
        # other nodes will verify that indeed the payer signed the tx
        self.signature: Signature = signature

    def get_id(self) -> TransactionID:
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
        # convert to TransactionID which is subtype of bytes
        return TransactionID(tx_hash)

    @property
    def is_coinbase(self) -> bool:
        """
        returns true iff this is a coinbase transaction which creates money
        """
        return self.input is None
