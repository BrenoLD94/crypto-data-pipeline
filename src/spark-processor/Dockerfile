FROM apache/spark-py:v3.4.0

WORKDIR /src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

CMD ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0", "processor.py"]