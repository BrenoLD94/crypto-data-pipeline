FROM apache/spark-py:v3.4.0

USER root

RUN groupadd -r spark && useradd --no-log-init -m -r -g spark spark

RUN chown -R spark:spark /home/spark
RUN mkdir -p /opt/spark/work-dir && chown -R spark:spark /opt/spark/work-dir
RUN mkdir -p /src/app && chown -R spark:spark /src/app

COPY --chown=spark:spark requirements.txt /src/app
COPY --chown=spark:spark app/ /src/app

WORKDIR /src/app

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /opt/spark/work-dir

USER spark