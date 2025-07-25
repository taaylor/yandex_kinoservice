ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && apt-get install -y curl build-essential netcat-openbsd \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app

RUN curl -sSL https://install.python-poetry.org | python3 - \
    && export PATH="/root/.local/bin:$PATH" \
    && poetry config virtualenvs.create false

ENV PATH="/root/.local/bin:${PATH}"

COPY services/event-generator/src/pyproject.toml services/event-generator/src/poetry.lock ./

COPY ../../libs/tracer_utils /opt/app/libs/tracer_utils
RUN cd /opt/app/libs/tracer_utils && poetry build && cd /opt/app && poetry add libs/tracer_utils

RUN poetry install --only main

COPY services/event-generator/src/ .

RUN chmod +x ./scripts/entrypoint.sh

RUN chmod +x ./scripts/run_celery.sh

CMD ["./scripts/entrypoint.sh"]
