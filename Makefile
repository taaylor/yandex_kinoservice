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


test-async-api-ci:
	docker compose -f $(COMPOSE_FILE_TEST) --profile async-api-test build --build-arg PYTHON_VERSION=$(PYTHON_VERSION)
	docker compose -f $(COMPOSE_FILE_TEST) --profile async-api-test run --rm tests-async-api /bin/bash -c ./tests/functional/start-tests.sh
	docker compose -f $(COMPOSE_FILE_TEST) --profile async-api-test down -v

test-auth-api-ci:
	docker compose -f $(COMPOSE_FILE_TEST) --profile auth-api-test build --build-arg PYTHON_VERSION=$(PYTHON_VERSION)
	docker compose -f $(COMPOSE_FILE_TEST) --profile auth-api-test run --rm tests-auth-api /bin/bash -c ./tests/functional/start-test.sh
	docker compose -f $(COMPOSE_FILE_TEST) --profile auth-api-test down -v

test-metrics-service-ci:
	docker compose -f $(COMPOSE_FILE_TEST) --profile metrics-api-test build --build-arg PYTHON_VERSION=$(PYTHON_VERSION)
	docker compose -f $(COMPOSE_FILE_TEST) --profile metrics-api-test run --rm tests-metrics-api /bin/bash -c ./tests/functional/start-test.sh
	docker compose -f $(COMPOSE_FILE_TEST) --profile metrics-api-test down -v
