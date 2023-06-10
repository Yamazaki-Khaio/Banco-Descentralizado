import json
import logging
import socket
import sys
from queue import Queue
import requests
from flask import Flask, request, jsonify
import threading
import pika




app = Flask(__name__)
# Obter o endereço IP da máquina local

def enviar_mensagem_fila_replicacao(data):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='fila_replicacao')
    channel.basic_publish(exchange='', routing_key='fila_replicacao', body=json.dumps(data).encode('utf-8'))
    connection.close()


def obeter_endereco_ip():
    return socket.gethostbyname(socket.gethostname())

# armazenar dados
contas = {}
bloqueios = {}
relogio = {}
fila_replicacao = Queue()
mutex = threading.Lock()
bloqueio_transferencia = threading.Lock()

log = logging.getLogger('registro_log')
log.setLevel(logging.INFO)
log_format = logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('registro_log')
file_handler.setFormatter(log_format)
log.addHandler(file_handler)

# Lista de URLs dos servidores
server_urls = [
    '192.168.3.2:5000',
    '192.168.3.2:5001',
    '192.168.3.2:5002',
    '192.168.3.2:5003',
    '192.168.3.2:5004',
]

def bakery_lock(id_conta):
    incrementar_relogio()
    endereco = request.remote_addr
    valor = relogio.get(endereco, 0)  # Obtém o valor do relógio para o endereço (ou 0 se a chave não existir)
    for outro_endereco, valor_outro in relogio.items():
        if (valor, outro_endereco) < (valor_outro, endereco):
            return False
        elif (valor, outro_endereco) == (valor_outro, endereco) and outro_endereco < endereco:
            return False
    return True


def bakery_unlock(id_conta):
    incrementar_relogio()


def get_available_port(start_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            s.bind(('localhost', start_port))
            s.close()
            return start_port
        except OSError:
            start_port += 1

# Read the command-line arguments
if len(sys.argv) > 1:
    # If a port number is provided as an argument, use it
    port = int(sys.argv[1])
else:
    # If no port number is provided, start from a default port and find an available port
    start_port = 5000  # Default start port
    port = get_available_port(start_port)

endereco_ip = "{}:{}".format(obeter_endereco_ip(), port)


# Função para incrementar o relógio vetorial
def incrementar_relogio():
    if endereco_ip in relogio:
        relogio[endereco_ip] += 1
    else:
        relogio[endereco_ip] = 1


# Classe para processar as operações de replicação em segundo plano
class ReplicacaoThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.replicando = True

    def run(self):
        while self.replicando:
            data = fila_replicacao.get()
            if data is None:
                break

            self.replicar_log(data)

    def replicar_log(self, data):
        incrementar_relogio()
        operacao = data.get('operacao')


        if operacao == 'criar_conta':
            id_conta = data.get('id_conta')
            saldo = data.get('saldo')

            if id_conta not in contas:
                contas[id_conta] = saldo
                bloqueios[id_conta] = threading.Lock()

        elif operacao == 'deposito':
            id_conta = data.get('id_conta')
            valor = data.get('valor')

            saldo = contas.get(id_conta)
            if saldo is not None:
                saldo += valor
                contas[id_conta] = saldo

        elif operacao == 'saque':
            id_conta = data.get('id_conta')
            valor = data.get('valor')

            saldo = contas.get(id_conta)
            if saldo is not None and valor <= saldo:
                saldo -= valor
                contas[id_conta] = saldo

        elif operacao == 'transferencia':
            id_origem = data.get('id_origem')
            id_destino = data.get('id_destino')
            valor = data.get('valor')

            saldo_origem = data.get(id_origem)
            saldo_destino = data.get(id_destino)

            if saldo_origem is not None and saldo_destino is not None and valor <= saldo_origem:
                saldo_origem -= valor
                saldo_destino += valor
                contas[id_origem] = saldo_origem
                contas[id_destino] = saldo_destino

        for url in server_urls:
            if url != endereco_ip:
                try:
                    response = requests.post(url + '/replicar', json=data)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    log.error(f'Erro ao replicar log para {url}: {e}')

        log.info(f'Operação replicada: {operacao} - {data} - Relógio lógico: {relogio}')

    def finalizar(self):
        self.replicando = False



@app.route('/', methods=['GET'])
def index():
    return '''
        <h1>Servidor de Contas Bancárias</h1>
        <p>API para criar, consultar e operar contas bancárias.</p>
    '''
@app.route('/log', methods=['GET'])
def visualizar_log():
    with open('registro_log', 'r') as file:
        log_content = file.read()

    return log_content

# Rota para criar uma nova conta bancária
@app.route('/contas', methods=['POST'])
def criar_conta():
    id_conta = request.json.get('id_conta')
    saldo = request.json.get('saldo')

    if id_conta is None or saldo is None:
        return jsonify({'sucesso': False, 'mensagem': 'Dados inválidos'})

    if id_conta in contas:
        return jsonify({'sucesso': False, 'mensagem': 'Conta já existe'})


    mutex.acquire()
    incrementar_relogio()
    contas[id_conta] = saldo
    bloqueios[id_conta] = threading.Lock()
    mutex.release()

    data = {
        'operacao': 'criar_conta',
        'id_conta': id_conta,
        'saldo': saldo,
        'relogio': relogio,
    }

    enviar_mensagem_fila_replicacao(data)
    return jsonify({'mensagem': 'Conta criada com sucesso'}), 200


# Rota para consultar o saldo de uma conta
@app.route('/contas/<id_conta>', methods=['GET'])
def consultar_saldo(id_conta):
    incrementar_relogio()
    saldo = contas.get(id_conta)
    with mutex:
        if saldo is None:
            return jsonify({'sucesso': False, 'mensagem': 'Conta não encontrada'})
        log.info('Consulta de saldo: ' + str(id_conta) + ' saldo: ' + str(saldo) + ' relogio logico: ' + str(relogio))

        return jsonify({'sucesso': True, 'saldo': saldo})


# função para saque e deposito
def realizar_transacao(id_conta, tipo_operacao):
    incrementar_relogio()
    valor = request.json.get('valor')
    with mutex:
        if id_conta not in contas:
            return jsonify({'sucesso': False, 'mensagem': 'Conta não encontrada'})
        bakery_lock(id_conta)
        saldo = contas[id_conta]
        if tipo_operacao == 'saque' and saldo < valor:
            bakery_unlock(id_conta)
            return jsonify({'sucesso': False, 'mensagem': 'Saldo insuficiente'})

        if tipo_operacao == 'deposito':
            contas[id_conta] += valor
        elif tipo_operacao == 'saque':
            contas[id_conta] -= valor

        bakery_unlock(id_conta)

    mensagem_sucesso = 'Depósito realizado' if tipo_operacao == 'deposito' else 'Saque realizado'
    data = {
        'operacao': tipo_operacao,
        'id_conta': id_conta,
        'valor': valor,
        'relogio': relogio,
    }
    enviar_mensagem_fila_replicacao(data)
    return jsonify({'sucesso': True, 'mensagem': mensagem_sucesso})


# Rota para realizar um depósito em uma conta
@app.route('/contas/<id_conta>/deposito', methods=['POST'])
def realizar_deposito(id_conta):
    return realizar_transacao(id_conta, 'deposito')


# Rota para realizar um saque em uma conta
@app.route('/contas/<id_conta>/saque', methods=['POST'])
def realizar_saque(id_conta):
    return realizar_transacao(id_conta, 'saque')


# rota para realizar transferencia
@app.route('/contas/<id_conta>/transferencia', methods=['POST'])
def transferencia(id_conta):
    incrementar_relogio()
    valor = request.json.get('valor')
    conta_destino = request.json.get('conta_destino')
    saldo_origem = contas[id_conta]
    if id_conta == conta_destino:
        return jsonify({'sucesso': False, 'mensagem': 'Conta de origem e destino são iguais'})

    with bloqueio_transferencia:
        with mutex:
            if id_conta not in contas:
                return jsonify({'sucesso': False, 'mensagem': 'Conta de origem não encontrada'})

            #transferencia local
            elif conta_destino in contas:
                if saldo_origem >= valor:
                    bakery_lock(id_conta)
                    bakery_lock(conta_destino)
                    contas[id_conta] -= valor
                    contas[conta_destino] += valor
                    bakery_unlock(id_conta)
                    bakery_unlock(conta_destino)
                    data = {
                        'operacao': 'transferencia',
                        'id_origem': id_conta,
                        'id_destino': conta_destino,
                        'valor': valor,
                        'relogio': relogio,
                    }
                    mensagem_sucesso = f'Transferência de {valor} para a conta {conta_destino} realizada'
                    enviar_mensagem_fila_replicacao(data)
                    return jsonify({'sucesso': True, 'mensagem': mensagem_sucesso})

            # Transferência entre servidores
            else:
                servidor_destino = request.json.get('servidor')

                if servidor_destino is None:
                    return jsonify({'sucesso': False, 'mensagem': 'Servidor não informado'})
                else:
                    url = f"http://{servidor_destino}/contas/{conta_destino}/deposito"
                    if saldo_origem >= valor:
                        bakery_lock(id_conta)
                        bakery_lock(conta_destino)
                        payload = {'valor': valor}
                        response = requests.post(url, json=payload)
                        if response.status_code == 200:
                            contas[id_conta] -= valor
                            bakery_unlock(id_conta)
                            bakery_unlock(conta_destino)

                            data = {
                                'operacao': 'transferencia',
                                'id_origem': id_conta,
                                'id_destino': conta_destino,
                                'valor': valor,
                                'relogio': relogio,
                            }

                        mensagem_sucesso = f'Transferência de {valor} para a conta {conta_destino} realizada'
                        enviar_mensagem_fila_replicacao(data)
                        return jsonify({'sucesso': True, 'mensagem': mensagem_sucesso})
                    else:
                        return jsonify({'sucesso': False, 'mensagem': 'Saldo insuficiente'})


    return jsonify({'sucesso': False, 'mensagem': 'Conta destino não encontrada'})


# rota para realizar transferencia remota
@app.route('/contas/<id_conta>/transferencia-remota', methods=['POST'])
def transferencia_remota(id_conta):
    incrementar_relogio()
    valor = request.json.get('valor')
    conta_destino = request.json.get('conta_destino')

    with bloqueio_transferencia:
        with mutex:
            if id_conta not in contas:
                return jsonify({'sucesso': False, 'mensagem': 'Conta de origem não encontrada'})

            if conta_destino not in contas:
                contas[id_conta] -= valor
                data = {
                    'operacao': 'transferencia',
                    'id_origem': id_conta,
                    'id_destino': conta_destino,
                    'valor': valor,
                    'relogio': relogio,
                }
                mensagem_sucesso = f'Transferência de {valor} para a conta {conta_destino} realizada'
                enviar_mensagem_fila_replicacao(data)
                return jsonify({'sucesso': True, 'mensagem': mensagem_sucesso})
            else:
                return jsonify({'sucesso': False, 'mensagem': 'Conta de destino já existe em outro servidor'})



# Rota para consultar o saldo de uma conta em outro servidor
@app.route('/saldo-outro-servidor/<id_conta>/<endereco_servidor>', methods=['GET'])
def consultar_saldo_outro_servidor(id_conta, endereco_servidor):
    url = f"http://{endereco_servidor}/contas/{id_conta}"
    response = requests.get(url)
    return response.json()


# Rota para realizar uma transação em outro servidor
@app.route('/transacao-outro-servidor', methods=['POST'])
def realizar_transacao_outro_servidor():
    dados = request.get_json()
    id_conta = dados['id_conta']
    valor = dados['valor']
    endereco_servidor = dados['endereco_servidor']

    url = f"http://{endereco_servidor}/contas/{id_conta}/deposito"
    payload = {'valor': valor}
    response = requests.post(url, json=payload)
    return response.json()

# Rota para replicar uma operação em outros servidores
@app.route('/replicar', methods=['POST'])
def replicar():
    incrementar_relogio()
    data = request.get_json()
    fila_replicacao.put(json.dumps(data))
    return jsonify({'sucesso': True, 'mensagem': 'Log replicado com sucesso'})


if __name__ == '__main__':
    replicacao_thread = ReplicacaoThread()
    replicacao_thread.start()

    log.info('Servidor iniciado: ' + obeter_endereco_ip() + ':' + str(port))

    app.run(host=obeter_endereco_ip(), port=port, debug=False)
    replicacao_thread.join()
