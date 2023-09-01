# KubeChat

KubeChat is a chat tool for KubeBlocks, it is used for Text2SQL, Text2CD, Text2CV, Text2Cluster, Chatbot and
troubleshooting. KubeChat adopts the open-source LLM for local serving, so it can promise 100% privacy.

# Development Guide

You should install Python 3.11 first.

* install poetry

```bash
pip3.11 install poetry
```

* enter poetry environment

```bash
poetry shell
```

* install dependencies

```bash
poetry install
```

* run the django service

```bash
make run-backend
```

* run the celery service

```bash
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python celery -A config.celery worker -l INFO --concurrency 1

```

* run the flower monitor service

```bash
make flower
```

# 依赖管理原则

* 可选依赖，只在需要的时候导入


