FROM apache/spark-py:v3.4.0

USER root

# Criamos um grupo 'spark' e um usuário 'spark' com um diretório home
RUN groupadd -r spark && useradd --no-log-init -r -g spark spark

# Cria o diretório de trabalho para o processo do Spark
RUN mkdir -p /opt/spark/work-dir

# Dá a posse desse diretório ao usuário 'spark'
RUN chown -R spark:spark /opt/spark/work-dir

# Define o diretório de trabalho para a NOSSA aplicação
WORKDIR /src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

USER spark

CMD ["spark-submit", "--conf", "spark.user=spark", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0", "processor.py"]