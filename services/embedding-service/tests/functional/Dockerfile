FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl build-essential netcat-openbsd \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN curl -sSL https://install.python-poetry.org | python3 - \
    && export PATH="/root/.local/bin:$PATH" \
    && poetry config virtualenvs.create false

ENV PATH="/root/.local/bin:${PATH}"
ENV PYTHONPATH="/opt"

COPY services/embedding-service/tests/functional/pyproject.toml ./
COPY services/embedding-service/tests/functional/poetry.lock ./

RUN poetry install --only main

COPY services/embedding-service/tests ./tests

RUN chmod +x ./tests/functional/start-tests.sh

ENTRYPOINT ["./tests/functional/start-tests.sh"]
