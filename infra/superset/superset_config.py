# /infra/superset/superset_config.py

import os

# 1. A Chave Secreta
# Lemos a variável 'SUPERSET_SECRET_KEY' que será passada do .env
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY")

# 2. O Banco de Metadados (Onde o Superset salva dashboards, etc.)
# Nós construímos a URI a partir das variáveis do Postgres

POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
# 'postgres' é o nome do serviço no docker-compose.yaml
POSTGRES_HOST = "postgres" 
# 'superset' é o banco que criamos manualmente
POSTGRES_DB = "superset" 

# Esta é a variável que o Superset PROCURA (e que eu errei o nome antes)
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:5432/{POSTGRES_DB}"
)

# 3. Permite o upload de arquivos (necessário para o Trino)
# Isso permite que você conecte ao Trino subindo um arquivo .json
# (Embora possamos não precisar, é uma boa prática)
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
}