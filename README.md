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

* run the backend server

```bash
make run-backend
```

* run the frontend server

put the .env file to /path/to/frontend/.env

```
AUTH0_DOMAIN=kubechat.jp.auth0.com
AUTH0_CLIENT_ID=G6RuQZZNaDorHGUEOv7Mgq1COqfryTB2
ASSETS_ENDPOINT=http://localhost:8001
API_ENDPOINT=http://127.0.0.1:8000
PORT=8001
PUBLIC_PATH=/
DATA_MOCK=true
```

```bash
make run-frontend
```


# TODO

* [ ] 前端支持批量上传文件
* [ ] 静态文件服务器和API服务器分离，支持跨域
* [ ] 支持数据库类型Collection
* [ ] 支持切换LLM
* [ ] Collection支持多个Chat
* [x] websocket auth0认证
* [ ] 异步优化
* [ ] 错误和异常处理优化
* [ ] 抽象Memory接口
* [ ] pyproject依赖优化，各种向量数据库和数据库的依赖改为可选
* [ ] 补充API测试用例
* [ ] 支持chat bot
* [ ] 源数据库替换为PG
* [ ] 聊天支持流式返回
* [ ] Auth0认证缓存