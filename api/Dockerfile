# build stage
FROM python:3.9.6-slim-buster as build-stage

WORKDIR /opt/app

COPY requirements.txt .

RUN apt-get update && apt-get install -y git gcc make && \
    pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /opt/wheels -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

# run stage
FROM python:3.9.6-slim-buster as run-stage

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONOPTIMIZE 1

WORKDIR /opt/app

COPY . .

COPY --from=build-stage /opt/wheels /wheels

RUN apt-get update && \
    pip install --upgrade pip && \
    pip install --no-cache /wheels/* && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 2000

CMD ["gunicorn", "--bind", "0.0.0.0:2000", "--worker-class", "gevent", "src.app:app"]
