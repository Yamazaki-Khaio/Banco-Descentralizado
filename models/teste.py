import requests
import threading

def criar_conta(id_conta, saldo):
    url = 'http://localhost:5000/contas'
    data = {'id_conta': id_conta, 'saldo': saldo}

    response = requests.post(url, json=data)
    print(response.json())

def realizar_deposito(id_conta, valor):
    url = f'http://localhost:5000/contas/{id_conta}/deposito'
    data = {'valor': valor}

    response = requests.post(url, json=data)
    print(response.json())

def realizar_saque(id_conta, valor):
    url = f'http://localhost:5000/contas/{id_conta}/saque'
    data = {'valor': valor}

    response = requests.post(url, json=data)
    print(response.json())

def realizar_transferencia(id_origem, id_destino, valor):
    url = 'http://localhost:5000/transferencia'
    data = {'id_origem': id_origem, 'id_destino': id_destino, 'valor': valor}

    response = requests.post(url, json=data)
    print(response.json())

def consultar_saldo(id_conta):
    url = f'http://localhost:5000/contas/{id_conta}'

    response = requests.get(url)
    print(response.json())

def teste_atomicidade_transferencia():
    # Criar contas
    criar_conta('conta1', 100)
    criar_conta('conta2', 50)

    # Função para realizar uma transferência
    def realizar_transferencia_concorrente(id_origem, id_destino, valor):
        realizar_transferencia(id_origem, id_destino, valor)

    # Criar threads para as transferências
    thread1 = threading.Thread(target=realizar_transferencia_concorrente, args=('conta1', 'conta2', 40))
    thread2 = threading.Thread(target=realizar_transferencia_concorrente, args=('conta1', 'conta2', 100))



    # Iniciar as threads
    thread1.start()
    thread2.start()


    # Esperar as threads terminarem
    thread1.join()
    thread2.join()


    # Consultar saldo após as transferências
    consultar_saldo('conta1')
    consultar_saldo('conta2')

# Executar o teste de atomicidade das transferências
teste_atomicidade_transferencia()
