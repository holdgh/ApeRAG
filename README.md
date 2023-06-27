# KubeChat
KubeChat is a chat tool for KubeBlocks, it is used for Text2SQL, Text2CD, Text2CV, Text2Cluster, Chatbot and troubleshooting. KubeChat adopts the open-source LLM for local serving, so it can promise 100% privacy. 


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

* build project
```bash
poetry build
```

* run the server
```bash
poetry run llmserver
```


# TODO

* [ ] 支持批量上传文件
* [ ] 静态文件服务器和API服务器分离，支持跨域
* [ ] 支持数据库类型Collection
* [ ] 支持切换LLM
* [ ] Collection支持多个Chat