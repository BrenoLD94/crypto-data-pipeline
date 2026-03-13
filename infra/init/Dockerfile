# baixa imagem da cofluent para ter os comandos kafka via CLI
FROM confluentinc/cp-kafka:7.6.1

USER root

# define diretório de trabalho
WORKDIR /src/infra

# copia script.sh para container
COPY --chmod=755 ./init.sh ./init.sh

# seta script como executável
RUN chmod +x /src/infra/init.sh

# https://github.com/minio/mc?tab=readme-ov-file
RUN curl https://dl.min.io/client/mc/release/linux-amd64/mc \
  -o /usr/local/bin/mc \
  && chmod +x /usr/local/bin/mc

RUN curl -O https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
 && chmod +x wait-for-it.sh

# executa o script 
CMD ["/src/infra/init.sh"]