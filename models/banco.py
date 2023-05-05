from models.conta import Conta
from models.blockchain import Blockchain

class Banco:
    def __init__(self, nome, blockchain):
        self.nome = nome
        self.blockchain = blockchain

    def criar_conta(self, numero_conta, cliente, banco_destino=None):
        conta = Conta(numero_conta, cliente, self, banco_destino)
        self.blockchain.criar_transacao(conta.to_dict())
        return conta

    def depositar(self, conta, valor):
        conta.depositar(valor)
        self.blockchain.criar_transacao(conta.to_dict())

    def sacar(self, conta, valor):
        if conta.saldo >= valor:
            conta.sacar(valor)
            self.blockchain.criar_transacao(conta.to_dict())
            return True
        else:
            return False

    def transferir(self, conta_origem, conta_destino, valor):
        if conta_origem.saldo >= valor:
            conta_origem.transferir(conta_destino, valor)
            self.blockchain.criar_transacao(conta_origem.to_dict())
            self.blockchain.criar_transacao(conta_destino.to_dict())
            return True
        else:
            return False