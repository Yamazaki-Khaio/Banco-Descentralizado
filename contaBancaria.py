from models.blockchain import Blockchain

# Cria uma instância da classe Blockchain
blockchain = Blockchain()

# Adiciona alguns nós na rede
blockchain.register_node("http://localhost:5000")
blockchain.register_node("http://localhost:5001")

# Realiza algumas transações
blockchain.nova_transacao("endereco1", "endereco2", 1.5)
blockchain.nova_transacao("endereco2", "endereco1", 0.5)

# Minera um novo bloco
last_block = blockchain.last_block
last_proof = last_block["proof"]
proof = blockchain.proof_of_work(last_proof)
previous_hash = blockchain.hash(last_block)
blockchain.novo_block(proof, previous_hash)

# Verifica se a cadeia de blocos é válida
assert blockchain.valid_chain(blockchain.chain)

# Resolve conflitos de cadeia com outros nós na rede
blockchain.resolve_conflicts()

# Adiciona mais transações
blockchain.nova_transacao("endereco1", "endereco3", 2.0)
blockchain.nova_transacao("endereco3", "endereco2", 1.0)

# Minera um novo bloco
last_block = blockchain.last_block
last_proof = last_block["proof"]
proof = blockchain.proof_of_work(last_proof)
previous_hash = blockchain.hash(last_block)
blockchain.novo_block(proof, previous_hash)

# Verifica se a cadeia de blocos é válida novamente
assert blockchain.valid_chain(blockchain.chain)
