# DeepRAG

DeepRAG is a chat tool for KubeBlocks, it is used for Text2SQL, Text2CD, Text2CV, Text2Cluster, Chatbot and
troubleshooting. DeepRAG adopts the open-source LLM for local serving, so it can promise 100% privacy.

# Development Guide

You should install Python 3.11 first.

* install poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
poetry self add poetry-plugin-shell	
```

* install dependencies

```bash
poetry env use 3.11
poetry lock
poetry install
```

* prepare configs

```bash
cp envs/.env.template .env
```

* prepare postgres/redis/qdrant/elasticsearch

```bash
make run-db
```

* run the django service

```bash
poetry shell
```

```
make run-backend
```

* run the celery service

```bash
poetry shell
```

```
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python celery -A config.celery worker -l INFO --pool gevent
```

* run the frontend

```
make run-backend
```


then open the deeprag frontend console: http://localhost:8001
