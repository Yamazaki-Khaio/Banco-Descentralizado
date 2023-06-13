import unittest
import threading
from flask import Flask, json, jsonify, request
from api import app

# Simulando a estrutura de dados 'contas'
contas = {
    'conta_origem_id': 100,
    'conta_destino_id': 50
}

# Simulando as funções bakery_lock e bakery_unlock
def bakery_lock(conta_id):
    pass

def bakery_unlock(conta_id):
    pass

class TransferenciaConcorrenciaTestCase(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_transferencia_concorrencia(self):
        # Define o número de solicitações concorrentes
        num_solicitacoes = 10

        # Define os dados da transferência
        payload = {
            'valor': 10,
            'conta_destino': 'conta_destino_id'
        }

        # Lista para armazenar as threads
        threads = []

        # Função que será executada por cada thread
        def realizar_transferencia():
            response = self.app.post('/contas/conta_origem_id/transferencia', json=payload)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(response.status_code, 200)
            self.assertTrue(data['sucesso'])
            self.assertEqual(data['mensagem'], 'Transferência de 10 para a conta conta_destino_id realizada')

        # Cria as threads e as adiciona à lista
        for _ in range(num_solicitacoes):
            thread = threading.Thread(target=realizar_transferencia)
            threads.append(thread)

        # Inicia todas as threads
        for thread in threads:
            thread.start()

        # Aguarda a conclusão de todas as threads
        for thread in threads:
            thread.join()

if __name__ == '__main__':
    unittest.main()
