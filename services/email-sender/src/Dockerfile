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

COPY services/email-sender/src/pyproject.toml services/email-sender/src/poetry.lock ./

RUN poetry install --only main

COPY services/email-sender/src/ .

RUN chmod +x ./scripts/run_email_sender.sh

CMD ["./scripts/run_email_sender.sh"]
