FROM python:3-slim

WORKDIR /src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# DEBUG 1: Como os arquivos chegaram?
RUN ls -l

# Copia o conteúdo da pasta 'app' (que tem main.py e wait-for-it.sh)
COPY app/ .

# Dá permissão de execução ao script
RUN chmod +x wait-for-it.sh

# DEBUG 2: A permissão foi aplicada?
RUN ls -l

# O ENTRYPOINT define o comando "wrapper" que espera pelo Kafka
ENTRYPOINT ["./wait-for-it.sh", "kafka:29092", "--"]

# O CMD define o comando principal que será executado APÓS o wrapper
CMD ["python", "main.py"]