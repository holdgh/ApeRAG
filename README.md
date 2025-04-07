# ApeRAG

ApeRAG is a RAG system focused on the deep understanding of documents and multimedia materials, the parallel construction of vector indexes, and the evaluation of retrieval performance. It also provides features such as workflow orchestration, LLM management, data source management, automatic synchronization, and office tool integration.


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
make run-frontend
```


then open the aperag frontend console: http://localhost:8001
