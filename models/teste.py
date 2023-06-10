
import requests

def test_routes(url1, url2):
    # Cria uma nova conta na instância 1
    create_account_url1 = f'{url1}/create_account'
    data = {'account_number': '123', 'initial_balance': 100}
    response = requests.post(create_account_url1, json=data)
    print(response.json())

    # Faz um depósito na conta criada na instância 1
    deposit_url1 = f'{url1}/deposit'
    data = {'account_number': '123', 'amount': 50}
    response = requests.post(deposit_url1, json=data)
    print(response.json())

    # Obtém o saldo da conta criada na instância 1
    balance_url1 = f'{url1}/balance/123'
    response = requests.get(balance_url1)
    print(response.json())

    # Obtém todas as contas da instância 1
    accounts_url1 = f'{url1}/accounts'
    response = requests.get(accounts_url1)
    print(response.json())

    # Obtém todas as contas da instância 2
    accounts_url2 = f'{url2}/accounts'
    response = requests.get(accounts_url2)
    print(response.json())

    # Faz uma requisição para obter os dados de todas as contas na instância 1
    accounts_from_server1_url2 = f'{url2}/accounts_from_server1'
    response = requests.get(accounts_from_server1_url2)
    print(response.json())



if __name__ == '__main__':
    # Define as URLs das instâncias do servidor Flask
    url1 = 'http://localhost:51636'  # URL da primeira instância
    url2 = 'http://localhost:51649'  # URL da segunda instância

    # Executa o teste das rotas
    test_routes(url1, url2)
