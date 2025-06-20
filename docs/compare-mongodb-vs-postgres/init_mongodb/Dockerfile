FROM debian:bookworm-slim

# Установка зависимостей для добавления репозитория
RUN apt-get update && apt-get install -y gnupg curl

# Добавление репозитория MongoDB
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-6.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-archive-keyring.gpg && \
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-archive-keyring.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/6.0 main" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Установка mongosh
RUN apt-get update && apt-get install -y mongodb-mongosh && rm -rf /var/lib/apt/lists/*

# Разрешения для скрипта инициализации (если он копируется в образ)
COPY ./init_mongodb/init-mongo.sh ./docker-entrypoint-initdb.d/init-mongo.sh
RUN chmod +x ./docker-entrypoint-initdb.d/init-mongo.sh

ENTRYPOINT [ "./docker-entrypoint-initdb.d/init-mongo.sh" ]
