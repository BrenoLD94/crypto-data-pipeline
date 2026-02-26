# Spark Processor – Streaming Crypto Data Pipeline

## 📌 Visão Geral

O `spark-processor` é o módulo responsável pelo processamento distribuído de dados em streaming da pipeline de criptomoedas.

Ele consome dados do Kafka, aplica transformações estruturadas, grava os dados brutos tratados no Iceberg (MinIO + Postgres Catalog) e envia agregações temporais para o InfluxDB.

O processamento é feito usando **Spark Structured Streaming em modo cluster standalone**.

---

# 🏗️ Arquitetura Interna

```
Kafka → Spark Streaming
            │
            ├── Iceberg (Data Lake - Cold Path)
            │
            └── InfluxDB (Hot Path - Time Series)
```

### Fluxo detalhado:

1. Leitura contínua de tópicos Kafka (`trades-*`)
2. Parsing JSON e normalização de schema
3. Escrita contínua no Iceberg (dados detalhados)
4. Aplicação de watermark + window aggregation
5. Escrita agregada no InfluxDB

---

# 📂 Estrutura do Módulo

```
spark-processor/
│
├── app/
│   ├── main.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   ├── schema/
│   │   └── schema.py
│   │
│   ├── sources/
│   │   └── kafka.py
│   │
│   ├── transform/
│   │   └── transformations.py
│   │
│   ├── sink/
│   │   ├── iceberg.py
│   │   └── influxdb.py
│   │
│   └── utils/
│       └── logging_config.py
│
├── Dockerfile
├── requirements.txt
└── README.md
```

---

# 🔎 Responsabilidades por Camada

### `sources/`

Contém a lógica de leitura do Kafka usando `readStream`.

### `transform/`

Aplica:

* Parsing JSON
* Cast de tipos
* Normalização de colunas
* Watermark
* Window aggregation

### `sink/`

Responsável por:

* Escrita no Iceberg (MinIO + JDBC Catalog)
* Escrita no InfluxDB

### `schema/`

Define schemas estruturados usados no parsing.

### `config/`

Centraliza variáveis e configurações do ambiente.

### `utils/`

Configuração de logging estruturado.


# 🚀 Execução

O processamento é iniciado via:

```bash
spark-submit
```

Configurado no `docker-compose.yml`.

A aplicação:

* Conecta ao Spark Master
* Inicia as queries de streaming
* Mantém o processo ativo com `awaitAnyTermination()`

---
