
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

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main

COPY src/ /opt/app/
# COPY entrypoint.sh /opt/app/
RUN chmod +x /opt/app/entrypoint.sh

CMD ["/opt/app/entrypoint.sh"]
# # COPY /src .
# COPY src/ /opt/app/

# CMD ["gunicorn", "main:app", "--config", "./core/gunicorn_conf.py"]
