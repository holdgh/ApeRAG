# KubeChat

KubeChat is a chat tool for KubeBlocks, it is used for Text2SQL, Text2CD, Text2CV, Text2Cluster, Chatbot and
troubleshooting. KubeChat adopts the open-source LLM for local serving, so it can promise 100% privacy.

# Development Guide

You should install Python 3.11 first.

* install poetry

```bash
pip3.11 install poetry
```

* install dependencies

```bash
poetry install
```

* prepare configs

```bash
cp envs/.env.template .env
```

* prepare frontend

```bash
make frontend.local.none
```

* prepare postgres/redis/qdrant/elasticsearch

```bash
make run-db
```

* run the django service

```bash
poetry shell

make run-backend
```

* run the celery service

```bash
poetry shell

PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python celery -A config.celery worker -l INFO --concurrency 1
```
