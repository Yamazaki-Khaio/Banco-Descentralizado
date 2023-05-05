class Transacao:
    def __init__(self, remetente, destinatario, valor, is_criacao_conta=False):
        self.remetente = remetente
        self.destinatario = destinatario
        self.valor = valor
        self.is_criacao_conta = is_criacao_conta

    def as_dict(self):
        return {"remetente": self.remetente, "destinatario": self.destinatario, "valor": self.valor}
