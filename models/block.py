import datetime
from typing import List


class Block:
    def __init__(self, index, timestamp, transacoes, previous_hash, proof):
        self.index = index
        self.timestamp = timestamp
        self.transacoes = transacoes
        self.previous_hash = previous_hash
        self.proof = proof

    def as_dict(self):
        return {"index": self.index, "timestamp": self.timestamp, "transacoes": self.transacoes,
                "previous_hash": self.previous_hash, "proof": self.proof}