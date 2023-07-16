FROM python:3.9.6-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONOPTIMIZE 1

WORKDIR /opt/app

COPY pyproject.toml poetry.lock ./

RUN apt-get update &&  \
    apt-get install -y curl build-essential git && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install poetry && \
    poetry install

COPY . .

EXPOSE 2000

CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:2000", "--worker-class", "gevent", "src.app:app"]
