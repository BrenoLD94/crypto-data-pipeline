FROM apache/spark-py:v3.4.0

USER root

RUN groupadd -r spark && useradd --no-log-init -m -r -g spark spark

RUN chown -R spark:spark /home/spark
RUN mkdir -p /opt/spark/work-dir && chown -R spark:spark /opt/spark/work-dir
RUN mkdir -p /src/app && chown -R spark:spark /src/app

# COPY --chown=spark:spark ./jars/* /opt/spark/jars/

RUN apt-get update && apt-get install -y --no-install-recommends wget \
    && wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.23.19/bundle-2.23.19.jar\
    && wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.0/hadoop-aws-3.4.0.jar \
    && wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.4_2.12/1.9.2/iceberg-spark-runtime-3.4_2.12-1.9.2.jar \
    && wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.7/postgresql-42.7.7.jar \
    && wget -P /opt/spark/jars/  https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.4.0/spark-sql-kafka-0-10_2.12-3.4.0.jar \
    && wget -P /opt/spark/jars/  https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.0/kafka-clients-3.4.0.jar \
    && wget -P /opt/spark/jars/  https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar \
    && apt-get purge -y --auto-remove wget \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=spark:spark requirements.txt /src/app
COPY --chown=spark:spark app/ /src/app

WORKDIR /src/app

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /opt/spark/work-dir

USER spark