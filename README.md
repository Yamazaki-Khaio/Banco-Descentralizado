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
python api.py
O servidor será iniciado e estará pronto para receber requisições.

# Uso do sistema
O sistema de contas bancárias distribuído possui as seguintes rotas disponíveis:

POST /contas: Cria uma nova conta bancária. O corpo da requisição deve conter o ID da conta e o saldo inicial.

GET /contas/<id_conta>: Consulta o saldo de uma conta específica.

POST /contas/<id_conta>/deposito: Realiza um depósito em uma conta específica. O corpo da requisição deve conter o valor do depósito.

POST /contas/<id_conta>/saque: Realiza um saque em uma conta específica. O corpo da requisição deve conter o valor do saque.

POST /transferencia<id_conta>: Realiza uma transferência entre contas. O corpo da requisição deve conter o ID da conta de destino e o valor da transferência.

GET /saldo-outro-servidor/<id_conta>/<endereco_servidor>: Consulta o saldo de uma conta em outro servidor. O parâmetro id_conta é o ID da conta desejada e o parâmetro endereco_servidor é o endereço (URL) do servidor.

POST /transacao-outro-servidor: Realiza uma transação em outro servidor. O corpo da requisição deve conter o ID da conta, o valor da transação e o endereço do servidor.

# Introdução
Este código implementa um servidor de contas bancárias que permite a criação, consulta e operação de contas. O servidor utiliza a arquitetura distribuída para replicar operações em outros servidores, garantindo a consistência dos dados, utilizando a biblioteca pika para se comunicar com uma fila de mensagens RabbitMQ, permitindo a replicação assíncrona das operações em outros servidores.

# Metodologia
O código utiliza o framework Flask para criar um servidor web e expor APIs para interação com as contas bancárias. A comunicação entre os servidores é feita por meio do protocolo HTTP. Além disso, é utilizado o RabbitMQ para implementar uma fila de replicação de operações entre os servidores.
O servidor utiliza um mecanismo de bloqueio chamado Bakery Lock para garantir a consistência das operações concorrentes em uma mesma conta bancária.

# Objetivo
O objetivo deste código é fornecer uma solução distribuída para a criação, consulta e operação de contas bancárias. Ele permite a replicação de operações entre vários servidores, garantindo a consistência dos dados em um ambiente distribuído. O código é apenas uma implementação simples para fins academicos e pode ser utilizado como base para construir um sistema bancário distribuído com alta disponibilidade e escalabilidade.

# Contribuição
Contribuições são bem-vindas após o dia 20/06/2023! Sinta-se à vontade para abrir uma issue ou enviar um pull request com melhorias, correções de bugs ou novas funcionalidades para o projeto.
