# Bibliotecas necessárias
import datetime
import hashlib
import json
import threading
from threading import Lock
from urllib.parse import urlparse
import requests
import validators
import nltk
from nltk import word_tokenize

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')


# Definição da classe Blockchain
class Blockchain:

    def __init__(self):
        self.chain = []
        self.transacao_atual = []
        self.nodes = set()
        self.lock = Lock()
        # Cria o bloco genesis
        self.novo_block(previous_hash='1', proof=100)


    def novo_block(self, proof, previous_hash=None):
        """
        Cria um novo bloco na blockchain

        :param proof: int, prova de trabalho do bloco
        :param previous_hash: str, hash do bloco anterior
        :return: dict, novo bloco criado
        """
        with self.lock:
            block = {
                'index': len(self.chain) + 1,
                'timestamp': str(datetime.datetime.now()),
                'transacao': self.transacao_atual,
                'proof': proof,
                'previous_hash': previous_hash or self.hash(self.chain[-1]),
            }
        # Reseta a lista de transações correntes
        self.transacao_atual = []

        # Adiciona o bloco na cadeia de blocos
        self.chain.append(block)

        return block

    def nova_transacao(self, remetente, destinatario, valor):
        """
               Cria uma nova transação para entrar no próximo bloco minerado

               :param remetente: str, endereço do remetente
               :param destinatario: str, endereço do destinatário
               :param valor: double, quantidade a ser enviada
               :return: int, índice do bloco que irá armazenar a transação
               """
        with self.lock:
            tokens = word_tokenize(f"{remetente} {destinatario} {valor}")
            pos_tags = nltk.pos_tag(tokens)
            self.transacao_atual.append({
                'remente': remetente,
                'destinario': destinatario,
                'valor': valor,
                'pos_tags': pos_tags
            })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Retorna o hash SHA-256 do bloco

        :param block: Block, bloco a ser calculado o hash
        :return: str, hash SHA-256 do bloco
        """
        block_string = json.dumps(block, sort_keys=True).encode("utf-8")
        hash_object = hashlib.sha256(block_string)
        hash_hex = hash_object.hexdigest()
        return hash_hex

    @property
    def last_block(self):
        """
        Retorna o último bloco da blockchain

        :return: Block, último bloco da blockchain
        """
        return self.chain[-1]

    def proof_of_work(self, last_proof, num_threads=4):
        """
        Algoritmo de prova de trabalho:
         - Encontrar um número p' tal que hash(pp') contenha 4 zeros à esquerda, onde p é a prova anterior e p' é a nova
         - p é a prova anterior e p' é a nova prova

        :param last_proof: Última prova
        :param num_threads: Número de threads a serem usadas (padrão: 4)
        :return: Nova prova
        """
        proofs = [last_proof] * num_threads  # criar uma lista com as últimas provas
        threads = []  # criar uma lista para armazenar as threads
        results = {}  # criar um dicionário para armazenar os resultados

        # definir a função que será executada em cada thread
        def find_proof(thread_id):
            proof = last_proof + thread_id
            while self.valid_proof(last_proof, proof) is False:
                proof += num_threads  # incrementar o contador da thread em num_threads
            results[thread_id] = proof  # armazenar o resultado no dicionário

        # iniciar as threads
        for i in range(num_threads):
            t = threading.Thread(target=find_proof, args=(i,))
            t.start()
            threads.append(t)

        # aguardar a finalização de todas as threads
        for t in threads:
            t.join()

        # retornar a prova encontrada com o menor número de iterações
        return min(results.values())
    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Valida a prova: Verifica se hash(last_proof, proof) contém 4 zeros à esquerda.

        :param last_proof: <int> Última prova
        :param proof: <int> Prova atual
        :return: <bool> True se correta e False se não.
        """
        guess = f'{last_proof}{proof}'.encode("utf-8")
        guess_hash = hashlib.sha256(guess).hexdigest()
        result = guess_hash[:4] == "0000"
        return result

    def register_node(self, address):
        """
        Registra um novo nó (node) na rede.

        :param address: Endereço do nó no formato 'http://<ip>:<porta>'.
        """
        if not validators.url(address):
            raise ValueError("Endereço inválido")
        parsed_url = urlparse(address)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise ValueError("URL inválida")
        self.nodes.add(parsed_url.netloc)

    def valid_block(self, block, previous_block):
        if not self.valid_proof(previous_block['proof'], block['proof']):
            return False

        if previous_block['index'] + 1 != block['index']:
            return False

        if self.hash(previous_block) != block['previous_hash']:
            return False

        return True

    def valid_chain(self, chain):
        """
        Verifica se uma cadeia de blocos (chain) é válida.

        :param chain: A cadeia de blocos a ser verificada.
        :return: True se a cadeia for válida, False caso contrário.
        """
        last_block = chain[0]
        for block in chain[1:]:
            if block['previous_hash'] != self.hash(last_block):
                return False

            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block

        return True

    def resolve_conflicts(self):
        """
        Resolve conflitos na rede, escolhendo a cadeia de blocos mais longa entre os nós da rede.

        :return: True se a cadeia foi substituída, False caso contrário.
        """
        nodes = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in nodes:
            try:
                response = requests.get(f'http://{node}/chain')
            except requests.exceptions.RequestException:
                continue

            if response.status_code == 200:
                length = response.json().get('length', 0)
                chain = response.json().get('chain', [])

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False