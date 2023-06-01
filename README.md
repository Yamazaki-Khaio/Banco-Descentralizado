# Sistema de Contas Bancárias Distribuído
Repositório referente ao PBL 3 de MI - Concorrência e conectividade, Sistema de bancos totalmente distribuído

Este arquivo contém as instruções para executar o sistema de contas bancárias distribuído. Certifique-se de seguir os passos abaixo para configurar o ambiente corretamente e executar o sistema com sucesso.

# Pré-requisitos
Antes de começar, é necessário ter alguns pré-requisitos instalados no seu ambiente:

Python 3.x
Flask
Requests
Certifique-se de ter essas dependências instaladas antes de prosseguir.

# Instalação
Para instalar o sistema de contas bancárias distribuído, siga as etapas abaixo:

Faça o download ou clone o repositório do projeto para o seu ambiente local.

Acesse o diretório do projeto através do terminal.

Crie um ambiente virtual (opcional) para isolar as dependências do projeto. Para isso, execute o comando python3 -m venv venv. Em seguida, ative o ambiente virtual com o comando source venv/bin/activate.

Instale as dependências do sistema executando o comando pip install -r requirements.txt.

# Configuração
Antes de executar o sistema, você pode fazer algumas configurações opcionais:

Porta do servidor: Por padrão, o servidor será executado na porta 5000. Caso deseje alterar a porta, defina a variável de ambiente PORT com o número da porta desejada.
Executando o sistema
Para iniciar o sistema de contas bancárias distribuído, execute o seguinte comando no terminal:

Copy code
python app.py
O servidor será iniciado e estará pronto para receber requisições.

# Uso do sistema
O sistema de contas bancárias distribuído possui as seguintes rotas disponíveis:

POST /contas: Cria uma nova conta bancária. O corpo da requisição deve conter o ID da conta e o saldo inicial.

GET /contas/<id_conta>: Consulta o saldo de uma conta específica.

POST /contas/<id_conta>/deposito: Realiza um depósito em uma conta específica. O corpo da requisição deve conter o valor do depósito.

POST /contas/<id_conta>/saque: Realiza um saque em uma conta específica. O corpo da requisição deve conter o valor do saque.

POST /transferencia: Realiza uma transferência entre contas. O corpo da requisição deve conter o ID da conta de origem, o ID da conta de destino e o valor da transferência.

GET /saldo-outro-servidor/<id_conta>/<endereco_servidor>: Consulta o saldo de uma conta em outro servidor. O parâmetro id_conta é o ID da conta desejada e o parâmetro endereco_servidor é o endereço (URL) do servidor.

POST /transacao-outro-servidor: Realiza uma transação em outro servidor. O corpo da requisição deve conter o ID da conta, o valor da transação e o endereço do servidor.

# Contribuição
Contribuições são bem-vindas após o dia 06/06/2023! Sinta-se à vontade para abrir uma issue ou enviar um pull request com melhorias, correções de bugs ou novas funcionalidades para o projeto.
