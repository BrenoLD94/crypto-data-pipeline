````markdown
---

# 🧪 Testes de Resiliência e Recuperação

Esta seção descreve os testes realizados e os testes que serão realizados para validar a tolerância a falhas do pipeline e o comportamento do Spark Structured Streaming em diferentes cenários de indisponibilidade.

Os testes abaixo simulam falhas reais de infraestrutura e verificam a capacidade de recuperação automática do sistema.

---

## 🔹 Teste 1 – Falha de Executor (Worker)

**Objetivo:**  
Validar o reprocessamento automático de tasks quando um executor é perdido.

### Comando

```bash
docker compose stop spark-worker1
````

### Resultado Esperado

* O Spark Master UI indica que um executor foi perdido.
* As tasks são reagendadas automaticamente.
* O streaming continua rodando.
* Não ocorre perda de dados.
* O processamento retoma normalmente quando o worker volta.

### Observação Técnica

O Cluster Manager (Standalone) detecta a perda do executor e realoca as tasks pendentes para outro executor disponível.

---

## 🔹 Teste 2 – Falha do Driver

**Objetivo:**
Validar recuperação do streaming via checkpoint.

### Comando

```bash
docker compose stop spark-processor
docker compose start spark-processor
```

### Resultado Esperado

* A aplicação reinicia.
* O Spark retoma a leitura a partir do último offset commitado no Kafka.
* O estado das janelas (state store) é restaurado.
* Não ocorre reprocessamento completo desde o início.

### Observação Técnica

O diretório de checkpoint garante:

* Recuperação de offsets
* Recuperação de estado das agregações stateful
* Continuidade do processamento

---

## 🔹 Teste 3 – Falha do InfluxDB (Hot Path)

**Objetivo:**
Validar o comportamento do sink quando o banco de séries temporais está indisponível.

### Comando

```bash
docker compose stop influxdb
```

### Resultado Esperado

* Erros de escrita são registrados no log.
* O Spark continua processando dados.
* O Hot Path fica temporariamente indisponível.
* Ao reiniciar o InfluxDB, as escritas voltam ao normal.

### Observação Técnica

A falha do sink não deve derrubar o streaming completo.
Caso esteja derrubando, o tratamento de exceção deve ser revisado.

---

## 🔹 Teste 4 – Falha do Kafka

**Objetivo:**
Validar tolerância à indisponibilidade da fonte de dados.

### Comando

```bash
docker compose stop kafka-broker1
```

*(Se houver apenas um broker, pare o serviço kafka correspondente.)*

### Resultado Esperado

* O Spark entra em estado de retry.
* O streaming não morre imediatamente.
* Ao reiniciar o Kafka, o consumo é retomado automaticamente.
* A leitura continua do último offset confirmado.

### Observação Técnica

Structured Streaming mantém controle de offsets no checkpoint, garantindo retomada consistente.

---

## 🔹 Teste 5 – Purge Completo (Build do Zero)

**Objetivo:**
Validar que o projeto é totalmente reprodutível a partir da documentação.

### Comando

```bash
docker compose down -v
docker system prune -f
docker compose up --build -d
```

### Resultado Esperado

* Todos os serviços sobem corretamente.
* Tabelas Iceberg são criadas automaticamente.
* O streaming inicia sem intervenção manual.
* Dashboards funcionam corretamente.

### Observação Técnica

Este teste valida:

* Documentação correta
* Infraestrutura declarativa consistente
* Ausência de dependência de estado oculto

---

# 📋 Checklist de Validação Final

Antes de abrir Pull Request para `main`, valide:

## Estabilidade

* [ ] Pipeline sobe do zero
* [ ] Tabela Iceberg criada automaticamente
* [ ] Escrita no Influx funcionando
* [ ] Dashboard Grafana atualizado em tempo real

## Resiliência

* [ ] Worker pode morrer sem interromper pipeline
* [ ] Driver pode reiniciar e retomar do checkpoint
* [ ] Kafka pode reiniciar sem perda de dados
* [ ] Influx pode reiniciar sem quebrar o streaming

## Reprodutibilidade

* [ ] Projeto sobe com `docker compose up --build`
* [ ] README contém todas as instruções necessárias
* [ ] Nenhum passo manual oculto é necessário

---