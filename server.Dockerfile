FROM python:3.11

WORKDIR /app

RUN pip install --upgrade --no-cache-dir pip
RUN pip install --no-cache-dir poetry

COPY pyproject.toml ./

RUN poetry config virtualenvs.create false
RUN poetry install --only main --no-interaction --no-ansi --no-cache

RUN apt-get update \
    && apt-get -y install libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

COPY server/ ./server

CMD ["poetry", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]