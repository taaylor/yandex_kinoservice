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
	docker compose -f $(COMPOSE_FILE) --profile production up -d --build content-actions-api mongodb_router auth-api postgres pg-import jaeger glitchtip-postgres glitchtip-redis glitchtip-web glitchtip-worker glitchtip-migrate$(srv)

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

# Rabbit only
up-rabbit:
	docker compose up -d --build rabbitmq-1 rabbitmq-2 rabbitmq-3 rabbit-init nginx && \
	echo "ui on: http://127.0.0.1:4444/"

up-rabbit-logs:
	docker compose up -d --build rabbitmq-1 rabbitmq-2 rabbitmq-3 rabbit-init nginx && \
	docker compose logs -f rabbitmq-1

down-rabbit:
	docker compose down -v rabbitmq-1 rabbitmq-2 rabbitmq-3 rabbit-init nginx

# Notification service
up-notification:
	docker compose --profile production up --build -d postgres pg-import auth-api async-api jaeger nginx notification

up-notification-logs:
	docker compose --profile production up --build -d postgres pg-import auth-api content-actions-api async-api jaeger nginx notification && \
	docker compose logs -f $(srv)

down-notification:
	docker compose --profile production down postgres pg-import auth-api async-api jaeger nginx notification

down-notification-v:
	docker compose --profile production down -v postgres pg-import auth-api async-api jaeger nginx notification

# ws sender
ws-sender-start:
	docker compose up --build -d rabbit-init nginx ws-sender-worker redis postgres pg-import auth-api jaeger notification async-api
	docker compose logs -f ws-sender-worker


# event-generator
event-generator-up:
	docker compose -f $(COMPOSE_FILE) up --build -d async-api es-init kibana nginx rabbit-init notification event-generator celery-beat

event-generator-down-v:
	docker compose -f $(COMPOSE_FILE) down -v async-api es-init kibana nginx rabbit-init elasticsearch redis notification event-generator celery-beat postgres

event-generator-reload:
	docker compose -f $(COMPOSE_FILE) down -v async-api es-init kibana nginx rabbitmq-1 rabbitmq-2 rabbitmq-3 rabbit-init elasticsearch redis notification event-generator celery-beat postgres && docker compose -f $(COMPOSE_FILE) up --build -d async-api es-init kibana nginx rabbitmq-1 rabbitmq-2 rabbitmq-3 rabbit-init notification-api event-generator celery-beat

up-link:
	docker compose --profile production up --build -d postgres link nginx

up-link-logs:
	docker compose --profile production up --build -d postgres link nginx && \
	docker compose logs -f $(srv)

down-link-v:
	docker compose --profile production down -v postgres link nginx

# Запуск всех сервисов контекста нотификаций
up-notification-context:
	docker compose --profile production up --build -d email-sender postgres pg-import rabbit-init redis ws-sender-worker link auth-api async-api jaeger nginx notification && \
	docker compose logs -f notification


# -=-=-=-=- EMAIL-SENDER SECTION -=-=-=-=-
up-email-sender:
	docker compose -f $(COMPOSE_FILE) up --build -d email-sender nginx notification pg-import

down-email-sender-v:
	docker compose -f $(COMPOSE_FILE) down -v email-sender rabbitmq-1 rabbitmq-2 rabbitmq-3 rabbit-init nginx notification pg-import auth-api redis postgres elasticsearch mailhog

reload-email-sender:
	docker compose -f $(COMPOSE_FILE) down -v email-sender rabbitmq-1 rabbitmq-2 rabbitmq-3 rabbit-init nginx notification pg-import auth-api redis postgres elasticsearch mailhog && docker compose -f $(COMPOSE_FILE) up --build -d email-sender nginx notification pg-import
