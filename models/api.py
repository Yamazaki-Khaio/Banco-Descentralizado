import json
import logging
import os
import socket
from queue import Queue
import requests
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)
# Obter o endereço IP da máquina local
local_ip = socket.gethostbyname(socket.gethostname())

# armazenar dados
contas = {}
bloqueios = {}
relogio = {}
log = logging.getLogger('registro_log')
log.setLevel(logging.INFO)
file_handler = logging.FileHandler('registro_log')
log.addHandler(file_handler)

# Lista de URLs dos servidores
server_urls = [
    'http://localhost:5000',
    'http://192.168.3.2:5000',
    'http://localhost:5002',
    'http://localhost:5003',
    'http://localhost:5004'
]

def get_available_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    _, port = s.getsockname()
    s.close()
    return port

# Fila de mensagens para replicação do log
fila_replicacao = Queue()

# mutex para exclusão mútua
mutex = threading.Lock()


# Função para incrementar o relógio vetorial
def incrementar_relogio():
    with mutex:
        if request.remote_addr in relogio:
            relogio[request.remote_addr] += 1
        else:
            relogio[request.remote_addr] = 1


# Classe para processar as operações de replicação em segundo plano
class ReplicacaoThread(threading.Thread):
    def __init__(self):
        super(ReplicacaoThread, self).__init__()

    def run(self):
        while True:
            data = fila_replicacao.get()
            if data is None:
                break

            self.replicar_log(data)

    def replicar_log(self, data):
        incrementar_relogio()
        data_dict = json.loads(data)
        operacao = data_dict['operacao']


        if operacao == 'criar_conta':
            id_conta = data_dict['id_conta']
            saldo = data_dict['saldo']

            if id_conta not in contas:
                contas[id_conta] = saldo
                bloqueios[id_conta] = threading.Lock()

        elif operacao == 'deposito':
            id_conta = data_dict['id_conta']
            valor = data_dict['valor']

            saldo = contas.get(id_conta)
            if saldo is not None:
                saldo += valor
                contas[id_conta] = saldo

        elif operacao == 'saque':
            id_conta = data_dict['id_conta']
            valor = data_dict['valor']

            saldo = contas.get(id_conta)
            if saldo is not None and valor <= saldo:
                saldo -= valor
                contas[id_conta] = saldo

        elif operacao == 'transferencia':
            id_origem = data_dict['id_origem']
            id_destino = data_dict['id_destino']
            valor = data_dict['valor']

            saldo_origem = contas.get(id_origem)
            saldo_destino = contas.get(id_destino)

            if saldo_origem is not None and saldo_destino is not None and valor <= saldo_origem:
                saldo_origem -= valor
                saldo_destino += valor
                contas[id_origem] = saldo_origem
                contas[id_destino] = saldo_destino

        for url in server_urls:
            if url != local_ip:
                try:
                    response = requests.post(url + '/replicar', json=data_dict)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    log.error(f'Erro ao replicar log para {url}: {e}')

        log.info(f'Operação replicada: {operacao} - {data} - Relógio lógico: {relogio}')

    def finalizar(self):
        fila_replicacao.put(None)


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
    incrementar_relogio()
    dados = request.get_json()
    id_conta = dados.get('id_conta')
    saldo = dados.get('saldo')

    if id_conta is None or saldo is None:
        return jsonify({'sucesso': False, 'mensagem': 'Dados inválidos'})

    if id_conta in contas:
        return jsonify({'sucesso': False, 'mensagem': 'Conta já existe'})

    with mutex:
        contas[id_conta] = saldo
        bloqueios[id_conta] = threading.Lock()

        log.info('Conta criada: ' + str(id_conta) + ' saldo: - ' + str(saldo) + ' relogio logico: ' + str(relogio))
        fila_replicacao.put({'operacao': 'criar_conta', 'id_origem': id_conta, 'saldo': saldo, 'relogio': relogio})
    return jsonify({'sucesso': True, 'mensagem': 'Conta criada'})


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
    dados = request.get_json()
    with mutex:
        if dados is None:
            return jsonify({'sucesso': False, 'mensagem': 'Dados inválidos'})

        valor = dados.get('valor')

        if valor is None:
            return jsonify({'sucesso': False, 'mensagem': 'Valor inválido'})

        saldo = contas.get(id_conta)

        if saldo is None:
            return jsonify({'sucesso': False, 'mensagem': 'Conta não encontrada'})

        if tipo_operacao == 'deposito':
            saldo += valor

        elif tipo_operacao == 'saque':
            if valor > saldo:
                return jsonify({'sucesso': False, 'mensagem': 'Saldo insuficiente'})
            saldo -= valor

        contas[id_conta] = saldo
        log.info(
            tipo_operacao.capitalize() + ' realizado: ' + str(id_conta) + ' - ' + str(valor) + ' - ' + str(relogio))
        fila_replicacao.put({'operacao': tipo_operacao, 'id_conta': id_conta, 'valor': valor, 'relogio': relogio})

        if tipo_operacao == 'deposito':
            mensagem_sucesso = 'Depósito realizado'
        elif tipo_operacao == 'saque':
            mensagem_sucesso = 'Saque realizado'

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
@app.route('/transferencia', methods=['POST'])
def realizar_transferencia():
    incrementar_relogio()
    dados = request.get_json()
    id_origem = dados['id_origem']
    id_destino = dados['id_destino']
    valor = dados['valor']
    with mutex:
        if id_origem not in contas or id_destino not in contas:
            return jsonify({'sucesso': False, 'mensagem': 'Conta(s) não encontrada(s)'})

        saldo_origem = contas[id_origem]
        if saldo_origem < valor:
            return jsonify({'sucesso': False, 'mensagem': 'Saldo insuficiente na conta de origem'})
        with bloqueios[id_origem]:
            with bloqueios[id_destino]:
                # Realizar a transferência
                saldo_origem -= valor
                contas[id_origem] -= valor
                contas[id_destino] += valor

        log.info(
            'Transferência realizada: ' + str(id_origem) + ' -> ' + str(id_destino) + ' - ' + str(valor) + ' - ' + str(
                relogio))
        fila_replicacao.put(
            {'operacao': 'transferencia', 'id_origem': id_origem, 'id_destino': id_destino, 'valor': valor,
             'relogio': relogio})

        return jsonify({'sucesso': True, 'mensagem': 'Transferência realizada com sucesso'})


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


@app.route('/replicar', methods=['POST'])
def replicar():
    data = request.get_json()
    fila_replicacao.put(json.dumps(data))
    return jsonify({'message': 'Operação recebida para replicação'})


# Configuração do log de registro de operações do servidor
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    port = get_available_port()
    log.info('Servidor iniciado: ' + local_ip + ':' + port)
    # Verificar se foi passado o número de porta como argumento

    # Iniciar a thread de replicação em segundo plano
    replicacao_thread = ReplicacaoThread()
    replicacao_thread.start()

    app.run(host=local_ip, port=port, debug=True)
    replicacao_thread.finalizar()
    replicacao_thread.join()