import json
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from kafka import KafkaConsumer, KafkaProducer

# Configuração do Kafka
KAFKA_SERVERS = ['localhost:9092']
KAFKA_TOPIC = 'conta'
KAFKA_GROUP_ID = 'my-group-id'
KAFKA_AUTO_OFFSET_RESET = 'earliest'

producer_config = {
    'bootstrap_servers': KAFKA_SERVERS,
    'value_serializer': lambda x: json.dumps(x).encode('utf-8')
}

consumer_config = {
    'bootstrap_servers': KAFKA_SERVERS,
    'auto_offset_reset': KAFKA_AUTO_OFFSET_RESET,
    'group_id': KAFKA_GROUP_ID,
    'value_deserializer': lambda x: json.loads(x.decode('utf-8'))
}

producer = KafkaProducer(**producer_config)
consumer = KafkaConsumer(KAFKA_TOPIC)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app)

# Rotas para realizar operações bancárias
@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/saldo', methods=['GET'])
def consultar_saldo():
    id_conta = request.args.get('id_conta')
    message = next(consumer)
    while message is not None and message.key != id_conta:
        message = next(consumer, None)
    if message is None:
        return jsonify({'sucesso': False, 'mensagem': 'Conta não encontrada'})
    if message.topic == KAFKA_TOPIC and message.value['tipo'] == 'saldo' and message.value['id_conta'] == id_conta:
        saldo = message.value['saldo']
        return jsonify({'sucesso': True, 'saldo': saldo})
    return jsonify({'sucesso': False, 'mensagem': 'Conta não encontrada'})

@app.route('/deposito', methods=['POST'])
def realizar_deposito():
    dados = request.get_json()
    producer.send(KAFKA_TOPIC, {'tipo': 'deposito', 'id_conta': dados['id_conta'], 'valor': dados['valor']})
    return jsonify({'sucesso': True, 'mensagem': 'Depósito realizado com sucesso'})

@app.route('/saque', methods=['POST'])
def realizar_saque():
    dados = request.get_json()
    producer.send(KAFKA_TOPIC, {'tipo': 'saque', 'id_conta': dados['id_conta'], 'valor': dados['valor']})
    return jsonify({'sucesso': True, 'mensagem': 'Saque realizado com sucesso'})

@app.route('/transferencia', methods=['POST'])
def realizar_transferencia():
    dados = request.get_json()
    producer.send(KAFKA_TOPIC, {'tipo': 'transferencia', 'id_origem': dados['id_origem'], 'id_destino': dados['id_destino'], 'valor': dados['valor']})
    return jsonify({'sucesso': True, 'mensagem': 'Transferência realizada com sucesso'})


# SocketIO events
@socketio.on('consulta_saldo')
def handle_consulta_saldo(id_conta):
    producer.send('conta', {'tipo': 'consulta_saldo', 'id_conta': id_conta})

@socketio.on('realizar_deposito')
def handle_realizar_deposito(dados):
    id_conta = dados['id_conta']
    valor = dados['valor']
    producer.send('conta', {'tipo': 'deposito', 'id_conta': id_conta, 'valor': valor})

@socketio.on('realizar_saque')
def handle_realizar_saque(dados):
    id_conta = dados['id_conta']
    valor = dados['valor']
    producer.send('conta', {'tipo': 'saque', 'id_conta': id_conta, 'valor': valor})

@socketio.on('realizar_transacao')
def handler_realizar_transacao(dados):
    id_origem = dados['id_origem']
    id_destino = dados['id_destino']
    valor = dados['valor']
    producer.send('conta', {'tipo': 'transferencia', 'id_origem': id_origem, 'id_destino': id_destino, 'valor': valor})



if __name__ == 'main':
    socketio.run(app, host='0.0.0.0', port=5000)