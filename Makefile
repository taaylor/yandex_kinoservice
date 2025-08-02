COMPOSE_FILE = docker-compose.yml
COMPOSE_FILE_DEBUG = docker-compose.debug.yml
COMPOSE_FILE_TEST = docker-compose-tests.yml
COMPOSE_METRIC = docker-compose-metrics.yml
PYTHON_VERSION ?= 3.12
# Можно указать конкретный серви или не указывать и команда будет выполнена для всех сервисов
# Например: make up-logs srv=auth-api
srv ?=

# Запуск контейнеров в фоновом режиме
up:
	docker compose -f $(COMPOSE_FILE) --profile production up -d --build $(srv)

# Остановка контейнеров
down:
	docker compose -f $(COMPOSE_FILE) --profile production down $(srv)

# Остановка контейнеров и удаление волуме
down-v:
	docker compose -f $(COMPOSE_FILE) --profile production down -v $(srv)

# Запустить проект и посмотреть логи опредёлнного сервиса
up-logs:
	docker compose -f $(COMPOSE_FILE) --profile production up -d --build && docker compose -f $(COMPOSE_FILE) logs -f $(srv)

# Просмотр логов
logs:
	docker compose -f $(COMPOSE_FILE) logs -f $(srv)

# Запуск тестов async-api
test-async-api:
	docker compose -f $(COMPOSE_FILE_TEST) --profile async-api-test up --build -d
	docker compose -f $(COMPOSE_FILE_TEST) logs -f tests-async-api
	docker compose -f $(COMPOSE_FILE_TEST) --profile async-api-test down -v

# Запуск тестов auth-api
test-auth-api:
	docker compose -f $(COMPOSE_FILE_TEST) --profile auth-api-test up --build -d
	docker compose -f $(COMPOSE_FILE_TEST) logs -f tests-auth-api
	docker compose -f $(COMPOSE_FILE_TEST) --profile auth-api-test down -v

# Запуск тестов metrics-api
test-metrics-service:
	docker compose -f $(COMPOSE_FILE_TEST) --profile metrics-api-test up --build -d
	docker compose -f $(COMPOSE_FILE_TEST) logs -f tests-metrics-api
	docker compose -f $(COMPOSE_FILE_TEST) --profile metrics-api-test down -v

# Запуск тестов content-api-test
test-content-service:
	docker compose -f $(COMPOSE_FILE_TEST) --profile content-api-test up --build -d
	docker compose -f $(COMPOSE_FILE_TEST) --profile content-api-test run --rm tests-content-api /bin/bash -c ./tests/functional/start-tests.sh
	docker compose -f $(COMPOSE_FILE_TEST) --profile content-api-test down -v

test-async-api-ci:
	docker compose -f $(COMPOSE_FILE_TEST) --profile async-api-test build --build-arg PYTHON_VERSION=$(PYTHON_VERSION)
	docker compose -f $(COMPOSE_FILE_TEST) --profile async-api-test run --rm tests-async-api /bin/bash -c ./tests/functional/start-tests.sh
	docker compose -f $(COMPOSE_FILE_TEST) --profile async-api-test down -v

test-auth-api-ci:
	docker compose -f $(COMPOSE_FILE_TEST) --profile auth-api-test build --build-arg PYTHON_VERSION=$(PYTHON_VERSION)
	docker compose -f $(COMPOSE_FILE_TEST) --profile auth-api-test run --rm tests-auth-api /bin/bash -c ./tests/functional/start-tests.sh
	docker compose -f $(COMPOSE_FILE_TEST) --profile auth-api-test down -v

test-metrics-service-ci:
	docker compose -f $(COMPOSE_FILE_TEST) --profile metrics-api-test build --build-arg PYTHON_VERSION=$(PYTHON_VERSION)
	docker compose -f $(COMPOSE_FILE_TEST) --profile metrics-api-test run --rm tests-metrics-api /bin/bash -c ./tests/functional/start-tests.sh
	docker compose -f $(COMPOSE_FILE_TEST) --profile metrics-api-test down -v

test-content-service-ci:
	docker compose -f $(COMPOSE_FILE_TEST) --profile content-api-test build --build-arg PYTHON_VERSION=$(PYTHON_VERSION)
	docker compose -f $(COMPOSE_FILE_TEST) --profile content-api-test run --rm tests-content-api /bin/bash -c ./tests/functional/start-tests.sh
	docker compose -f $(COMPOSE_FILE_TEST) --profile content-api-test down -v

# -=-=-=-=- Секция content-actions-service -=-=-=-=-
content-service-up:
	docker compose -f $(COMPOSE_FILE) --profile production up -d --build content-actions-api mongodb_router auth-api postgres pg-import jaeger glitchtip-postgres glitchtip-redis glitchtip-web glitchtip-worker glitchtip-migrate$(srv) kafka-0 kafka-1 kafka-2 ui kafka-init nginx


content-service-low:
	docker compose -f $(COMPOSE_FILE) up -d --build content-actions-api mongodb_router auth-api postgres pg-import kafka-0 kafka-1 kafka-2 ui kafka-init nginx

# Остановка контейнеров и удаление волуме
content-service-down-v:
	docker compose -f $(COMPOSE_FILE) --profile production down -v content-actions-api redis mongodb_sh1_rep1 mongodb_sh1_rep2 mongodb_sh1_rep3 mongodb_sh2_rep1 mongodb_sh2_rep2 mongodb_sh2_rep3 mongodb_cfg1 mongodb_cfg2 mongodb_cfg3 mongodb_router mongodb_init auth-api postgres pg-import jaeger $(srv)

content-api:
	docker compose --profile production up --build -d content-actions-api

content-stop:
	docker compose --profile production down content-actions-api

# Локальный запуск сервисов при разработке
up-local-content-api:
	cd services/content-actions-service/src/ && uvicorn main:app --port 8009 --reload

up-local-notification:
	cd services/notification-service/src/ && uvicorn main:app --port 8009 --reload

up-local-auth:
	cd services/auth-service/src/ && uvicorn main:app --port 8009 --reload

up-local-link:
	cd services/short-link-service/src/ && uvicorn main:app --port 8009 --reload

up-local-embedding:
	cd services/embedding-service/src/ && uvicorn main:app --port 8009 --reload

event-generator-local:
	cd services/event-generator/src/ && uvicorn main:app --port 8009 --reload

up-nl-consumer-local:
	cd services/nl-consumer/src/ && uvicorn main:app --port 8009 --reload

up-local-async-api:
	cd services/async-api/src/ && uvicorn main:app --port 8009 --reload


# Запуск всех сервисов контекста нотификаций
up-notification-context:
	docker compose --profile production up --build -d email-sender event-generator celery-beat postgres pg-import rabbit-init redis ws-sender-worker link auth-api async-api jaeger nginx notification && \
	docker compose logs -f notification

up-extend-async-api:
	docker compose -f docker-compose.yml up --build -d async-api auth-api kibana pg-import nginx elasticsearch es-init

down-extend-async-api:
	docker compose -f docker-compose.yml down -v async-api auth-api elasticsearch kibana es-init redis postgres pg-import nginx

fill-data-for-checking-extend-async-api:
	docker compose -f docker-compose.yml exec async-api python prepare_data_for_checking.py

# Запуск всех сервисов контекста нотификаций
up-recs-context:
	docker compose up -d --build kibana embedding-etl recs-profile nl-consumer nginx notification && \
	docker compose up -d --build pg-import && \
	docker compose logs -f recs-profile

up-clickhouse:
	docker compose --profile production up --build -d clickhouse-node1 clickhouse-node2 clickhouse-node3 clickhouse-node4 init_clickhouse zookeeper

up-metrics-service:
	docker compose --profile production up --build -d clickhouse-node1 clickhouse-node2 clickhouse-node3 clickhouse-node4 init_clickhouse zookeeper kafka-0 kafka-1 kafka-2 kafka-init metric-api etl

down-metrics-service:
	docker compose --profile production down -v clickhouse-node1 clickhouse-node2 clickhouse-node3 clickhouse-node4 init_clickhouse zookeeper kafka-0 kafka-1 kafka-2 kafka-init metric-api etl

up-local-statistic:
	cd services/statistic-service/src/ && uvicorn main:app --port 8009 --reload

up-statistic-service:
	docker compose --profile production up --build -d statistic-service clickhouse-node1 clickhouse-node2 clickhouse-node3 clickhouse-node4 init_clickhouse zookeeper

up-async-static-service:
	docker compose -f $(COMPOSE_FILE_DEBUG) --profile production up --build -d statistic-service clickhouse-node1 clickhouse-node2 clickhouse-node3 clickhouse-node4 init_clickhouse zookeeper async-api auth-api kibana pg-import nginx elasticsearch es-init

vm-up-server:
	sudo docker compose --profile production up -d --build kibana embedding-etl recs-profile nl-consumer nginx notification auth-api pg-import postgres recs-profile embedding-service content-actions-api kafka-init statistic-service
