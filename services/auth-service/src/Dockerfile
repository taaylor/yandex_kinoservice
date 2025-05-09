FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl build-essential netcat-openbsd \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app

RUN curl -sSL https://install.python-poetry.org | python3 - \
    && export PATH="/root/.local/bin:$PATH" \
    && poetry config virtualenvs.create false

ENV PATH="/root/.local/bin:${PATH}"

COPY services/auth-service/src/pyproject.toml services/auth-service/src/poetry.lock ./

# Копируем libs и собираем на месте
COPY libs/auth_utils /opt/app/libs/auth_utils
RUN cd /opt/app/libs/auth_utils && poetry build && cd /opt/app && poetry add libs/auth_utils

COPY libs/tracer_utils /opt/app/libs/tracer_utils
RUN cd /opt/app/libs/tracer_utils && poetry build && cd /opt/app && poetry add libs/tracer_utils

RUN poetry install --only main

COPY services/auth-service/src/ .

RUN chmod +x ./scripts/entrypoint.sh

CMD ["./scripts/entrypoint.sh"]
