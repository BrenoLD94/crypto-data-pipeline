Crypto Data Pipeline
Este projeto implementa um pipeline de dados em tempo real para capturar, processar e visualizar dados de criptomoedas (BTC/USDT) da exchange Binance.

A arquitetura é baseada em microserviços orquestrados com Docker Compose e inclui:

Coleta: Um produtor Python que se conecta à API de WebSocket da Binance.
Ingestão: Apache Kafka para atuar como um buffer de mensagens resiliente.
Processamento: Apache Spark Streaming para realizar agregações e transformações em tempo real.
Armazenamento: InfluxDB, um banco de dados de série temporal, para armazenar os dados processados.
Visualização: Grafana para criar dashboards e visualizar os dados em tempo real.
Estrutura do Projeto
A organização dos arquivos e pastas segue o padrão de monorepo, separando o código da aplicação (src) das configurações de infraestrutura (infra).


/crypto-data-pipeline/
│
├── .env                    # Variáveis de ambiente para o Docker Compose (versões, etc.)
├── .gitignore              # Arquivos e pastas a serem ignorados pelo Git
├── docker-compose.yml      # O coração do projeto, orquestra todos os serviços
├── README.md               # Documentação principal do projeto
│
├── infra/                  # Configurações para serviços "prontos" (infraestrutura)
│   ├── grafana/
│   │   └── provisioning/
│   │       ├── dashboards/
│   │       │   ├── crypto-dashboard.json
│   │       │   └── dashboard.yml
│   │       └── datasources/
│   │           └── datasource.yml
│   └── influxdb/
│       └── init.sh         # Script inicial para criar o bucket/usuário no InfluxDB
│
└── src/                    # Nosso código customizado
    ├── producer/           # O script que pega dados da Binance
    │   ├── app/
    │   │   └── main.py
    │   ├── Dockerfile
    │   └── requirements.txt
    │
    └── spark-processor/      # O job de processamento do Spark
        ├── app/
        │   └── processor.py
        ├── Dockerfile
        └── requirements.txt

Detalhamento dos Diretórios
docker-compose.yml: Arquivo principal que define e conecta todos os serviços da aplicação (Kafka, Spark, Grafana, etc.).
.env: Armazena variáveis de ambiente não sensíveis, como versões de imagens Docker, para serem usadas no docker-compose.yml.
README.md: Este arquivo. A documentação central do projeto.
infra/: Contém arquivos de configuração para as ferramentas de terceiro que usamos.
grafana/provisioning: Configura o Grafana automaticamente na inicialização, criando a fonte de dados (datasource) para o InfluxDB e carregando os dashboards pré-definidos.
influxdb/init.sh: Script de inicialização para o InfluxDB, responsável por criar o bucket inicial, organização e tokens de acesso.
src/: Contém todo o código-fonte customizado desenvolvido para este projeto.
producer/: O microsserviço Python responsável por se conectar à API da Binance via WebSocket, capturar os dados e produzi-los em um tópico Kafka.
spark-processor/: O microsserviço contendo o job PySpark que consome os dados do Kafka, realiza o processamento e agregações, e salva o resultado no InfluxDB.
Como Executar