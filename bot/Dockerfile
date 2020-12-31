FROM python:3.8.6

WORKDIR /bot

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG 0

RUN apt -u update \
    && pip install poetry

COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && apt-get install python-psycopg2 -y \
    && apt-get install libjpeg-dev zlib1g-dev -y\
    && poetry install --no-interaction --no-ansi\
    && python -m spacy download en

COPY . .
