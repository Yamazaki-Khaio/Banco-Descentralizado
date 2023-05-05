from datetime import datetime
from models.blockchain import Blockchain
from models.block import Block

class Conta:
    def __init__(self, numero_conta, cliente):
        self.numero_conta = numero_conta
        self.cliente = cliente
        self.saldo = 0.0

    def depositar(self, valor):
        self.saldo += valor
        transacao = {
            "remetente": "Banco",
            "destinatario": self.numero_conta,
            "valor": valor,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        if not self.banco.blockchain.adicionar_transacao(transacao):
            return False
        self.transacoes.append(transacao)
        return True

    def sacar(self, valor):
        if valor > self.saldo:
            return False
        self.saldo -= valor
        transacao = {
            "remetente": self.numero_conta,
            "destinatario": "Banco",
            "valor": valor,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        if not self.banco.blockchain.adicionar_transacao(transacao):
            return False
        self.transacoes.append(transacao)
        return True

    def transferir(self, conta_destino, valor):
        if not self.sacar(valor):
            return False
        transacao = {
            "remetente": self.numero_conta,
            "destinatario": conta_destino.numero_conta,
            "valor": valor,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        if not conta_destino.banco.blockchain.adicionar_transacao(transacao):
            return False
        self.transacoes.append(transacao)
        return True
