import unittest
from models.blockchain import Blockchain


class TestBlockchain(unittest.TestCase):

    def setUp(self):
        self.bc = Blockchain()

    def test_novo_block(self):
        proof = 100
        previous_hash = '1'
        block = self.bc.novo_block(proof, previous_hash)

        self.assertTrue(isinstance(block, dict))
        self.assertTrue(isinstance(block['index'], int))
        self.assertTrue(isinstance(block['timestamp'], str))
        self.assertTrue(isinstance(block['transacao'], list))
        self.assertTrue(isinstance(block['proof'], int))
        self.assertTrue(isinstance(block['previous_hash'], str))
        self.assertEqual(block['index'], 2)
        self.assertEqual(block['proof'], proof)
        self.assertEqual(block['previous_hash'], previous_hash)

    def test_nova_transacao(self):
        remetente = 'endereco_remetente'
        destinatario = 'endereco_destinatario'
        valor = 10.0
        index = self.bc.nova_transacao(remetente, destinatario, valor)

        self.assertEqual(index, 2)
        self.assertEqual(len(self.bc.transacao_atual), 1)
        self.assertEqual(self.bc.transacao_atual[0]['remente'], remetente)
        self.assertEqual(self.bc.transacao_atual[0]['destinario'], destinatario)
        self.assertEqual(self.bc.transacao_atual[0]['valor'], valor)

    def test_hash(self):
        block = {
            'index': 1,
            'timestamp': '2022-05-04 11:30:00',
            'transacao': [],
            'proof': 1,
            'previous_hash': '1',
        }
        hash_result = self.bc.hash(block)
        self.assertEqual(len(hash_result), 64)

    def test_last_block(self):
        last_block = self.bc.last_block
        self.assertTrue(isinstance(last_block, dict))
        self.assertEqual(last_block['index'], 1)

    def test_proof_of_work(self):
        last_proof = 100
        new_proof = self.bc.proof_of_work(last_proof)
        self.assertTrue(isinstance(new_proof, int))
        self.assertTrue(self.bc.valid_proof(last_proof, new_proof))

    def test_valid_block(self):
        last_block = self.bc.last_block
        proof = self.bc.proof_of_work(last_block['proof'])
        block = self.bc.novo_block(proof, self.bc.hash(last_block))

        valid = self.bc.valid_block(block, last_block)
        self.assertIs(valid, True)

    def test_register_node(self):
        address = 'http://127.0.0.1:5000'
        self.bc.register_node(address)
        self.assertIn('127.0.0.1:5000', self.bc.nodes)


if __name__ == '__main__':
    unittest.main()
