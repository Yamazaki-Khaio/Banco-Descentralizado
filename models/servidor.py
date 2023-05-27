import logging
import os

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import sys
import threading
app = Flask(__name__)
socketio = SocketIO(app)

# Dicionário para armazenar as contas bancárias
contas = {}
bloqueios = {}
log = logging.getLogger('registro_log')
log.setLevel(logging.INFO)
file_handler = logging.FileHandler('regristro_log')
log.addHandler(file_handler)

# Variável para armazenar o relógio de Lamport
relogio = 0


#mutex para exclusão mútua
mutex = threading.Lock()

#função para recplicar log para os node
@socketio.on('replicar_log')
def replicar_log(data):
    global relogio
    with mutex:
        relogio = max(relogio, data['relogio']) + 1

    operacao = data['operacao']

    if operacao == 'criar_conta':
        id_conta = data['id_conta']
        saldo = data['saldo']

        if id_conta not in contas:
            contas[id_conta] = saldo
            bloqueios[id_conta] = threading.Lock()

    elif operacao == 'deposito':
        id_conta = data['id_conta']
        valor = data['valor']

        saldo = contas.get(id_conta)
        if saldo is not None:
            saldo += valor
            contas[id_conta] = saldo

    elif operacao == 'saque':
        id_conta = data['id_conta']
        valor = data['valor']

        saldo = contas.get(id_conta)
        if saldo is not None and valor <= saldo:
            saldo -= valor
            contas[id_conta] = saldo

    elif operacao == 'transferencia':
        id_origem = data['id_origem']
        id_destino = data['id_destino']
        valor = data['valor']

        saldo_origem = contas.get(id_origem)
        saldo_destino = contas.get(id_destino)

        if saldo_origem is not None and saldo_destino is not None and valor <= saldo_origem:
            saldo_origem -= valor
            saldo_destino += valor
            contas[id_origem] = saldo_origem
            contas[id_destino] = saldo_destino

    log.info(f'Operação replicada: {operacao} - {data} - Relógio lógico: {relogio}')


# Rota para criar uma nova conta bancária
@app.route('/contas', methods=['POST'])
def criar_conta():
    global relogio
    with mutex:
        relogio += 1
        dados = request.get_json()
        id_conta = dados.get('id_conta')
        saldo = dados.get('saldo')

    if id_conta is None or saldo is None:
        return jsonify({'sucesso': False, 'mensagem': 'Dados inválidos'})

    if id_conta in contas:
        return jsonify({'sucesso': False, 'mensagem': 'Conta já existe'})


    contas[id_conta] = saldo
    bloqueios[id_conta] = threading.Lock()
    #Emitir mensagem para replicar log da criação da conta
    socketio.emit('replicar_log', {'operacao': 'criar_conta', 'id_conta': id_conta, 'saldo': saldo, 'relogio': relogio})

    log.info('Conta criada: ' + str(id_conta) + ' saldo: - ' + str(saldo) + ' relogio logico: ' + str(relogio))
    return jsonify({'sucesso': True, 'mensagem': 'Conta criada'})

# Rota para consultar o saldo de uma conta
@app.route('/contas/<id_conta>', methods=['GET'])
def consultar_saldo(id_conta):
    global relogio
    with mutex:
        relogio += 1
        saldo = contas.get(id_conta)

    if saldo is None:
        return jsonify({'sucesso': False, 'mensagem': 'Conta não encontrada'})
    log.info('Consulta de saldo: ' + str(id_conta) + ' saldo: ' + str(saldo) + ' relogio logico: ' + str(relogio))
    # Emitir mensagem para replicar log da criação da conta
    socketio.emit('replicar_log', {'operacao': 'consulta_saldo', 'id_conta': id_conta, 'saldo': saldo, 'relogio': relogio})

    return jsonify({'sucesso': True, 'saldo': saldo})


# Rota para realizar um depósito em uma conta
@app.route('/contas/<id_conta>/deposito', methods=['POST'])
def realizar_deposito(id_conta):
    global relogio
    with mutex:
        relogio += 1
        dados = request.get_json()
        valor = dados.get('valor')

    if valor is None:
        return jsonify({'sucesso': False, 'mensagem': 'Valor inválido'})

    saldo = contas.get(id_conta)
    if saldo is None:
        return jsonify({'sucesso': False, 'mensagem': 'Conta não encontrada'})

    saldo += valor
    contas[id_conta] = saldo
    log.info('Depósito realizado: ' + str(id_conta) + ' - ' + str(valor) + ' - ' + str(relogio))
    socketio.emit('replicar_log', {'operacao': 'deposito', 'id_conta': id_conta, 'valor': valor, 'relogio': relogio})

    return jsonify({'sucesso': True, 'mensagem': 'Depósito realizado'})

# Rota para realizar um saque em uma conta
@app.route('/contas/<id_conta>/saque', methods=['POST'])
def realizar_saque(id_conta):
    global relogio
    with mutex:
        relogio += 1
        dados = request.get_json()
        valor = dados.get('valor')

    if valor is None:
        return jsonify({'sucesso': False, 'mensagem': 'Valor inválido'})

    saldo = contas.get(id_conta)
    if saldo is None:
        return jsonify({'sucesso': False, 'mensagem': 'Conta não encontrada'})

    if valor > saldo:
        return jsonify({'sucesso': False, 'mensagem': 'Saldo insuficiente'})

    saldo -= valor
    contas[id_conta] = saldo
    log.info('Saque realizado: ' + str(id_conta) + ' - ' + str(valor) + ' - ' + str(relogio))
    socketio.emit('replicar_log', {'operacao': 'saque', 'id_conta': id_conta, 'valor': valor, 'relogio': relogio})
    return jsonify({'sucesso': True, 'mensagem': 'Saque realizado'})

#rota para realizar transferencia
@app.route('/transferencia', methods=['POST'])
def realizar_transferencia():
    global relogio
    with mutex:
        relogio += 1

        dados = request.get_json()
        id_origem = dados['id_origem']
        id_destino = dados['id_destino']
    valor = dados['valor']

    if id_origem not in contas or id_destino not in contas:
        return jsonify({'sucesso': False, 'mensagem': 'Conta(s) não encontrada(s)'})


    saldo_origem = contas[id_origem]
    if saldo_origem < valor:
        return jsonify({'sucesso': False, 'mensagem': 'Saldo insuficiente na conta de origem'})

    with mutex:
        with bloqueios[id_origem]:
            with bloqueios[id_destino]:
                # Realizar a transferência
                saldo_origem -= valor
                contas[id_origem] -= valor
                contas[id_destino] += valor
    log.info('Transferência realizada: ' + str(id_origem) + ' -> ' + str(id_destino) + ' - ' + str(valor) + ' - ' + str(relogio))
    socketio.emit('replicar_log', {'operacao': 'transferencia', 'id_origem': id_origem, 'id_destino': id_destino, 'valor': valor, 'relogio': relogio})

    return jsonify({'sucesso': True, 'mensagem': 'Transferência realizada com sucesso'})

#Configuração do log de registro de operações do servidor
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    # Verificar se foi passado o número de porta como argumento
    if 'PORT' in os.environ:
        port = int(os.environ['PORT'])
    else:
        port = 5000  # Porta padrão

    socketio.run(app, port=port, host='0.0.0.0')
