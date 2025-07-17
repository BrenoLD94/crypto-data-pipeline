FROM python:3-slim

WORKDIR /src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Copia o conteúdo da pasta 'app' (que tem main.py e wait-for-it.sh)
COPY --chmod=755 app/ .

# O ENTRYPOINT define o comando "wrapper" que espera pelo Kafka
ENTRYPOINT ["./wait-for-it.sh", "kafka:29092", "--"]

# O CMD define o comando principal que será executado APÓS o wrapper
CMD ["python", "main.py"]