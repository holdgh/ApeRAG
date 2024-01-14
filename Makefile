VERSION ?= v0.1.2
VERSION_FILE ?= version/__init__.py
LLMSERVER_VERSION ?= v0.1.1
BUILDX_PLATFORM ?= linux/amd64
BUILDX_ARGS ?= --sbom=false --provenance=false
REGISTRY ?= registry.cn-hangzhou.aliyuncs.com
FRONTEND_BRANCH ?= main
FRONTEND_REPO_DIR ?= /tmp/KubeChat-FrontEnd

init:
	cp envs/.env.template .env
	cp envs/.env.frontend.template .env.frontend

.PHONY: version
version:
	@git rev-parse HEAD | cut -c1-7 > commit_id.txt
	@echo "VERSION = '$(VERSION)'" > $(VERSION_FILE)
	@echo "GIT_COMMIT_ID = '$$(cat commit_id.txt)'" >> $(VERSION_FILE)
	@rm commit_id.txt

build-requirements:
	sh scripts/export-requirements.sh

image: build-requirements version
	docker buildx build -t $(REGISTRY)/apecloud/kubechat:$(VERSION) --platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) --push -f ./Dockerfile  .

llm-server-image: build-requirements version
	docker buildx build -t $(REGISTRY)/apecloud/kubechat-llmserver:$(LLMSERVER_VERSION) --platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) --push -f ./Dockerfile-llmserver  .

diff:
	@python manage.py diffsettings

migrate:
	@python manage.py makemigrations
	@python manage.py migrate

run-redis:
	@echo "Starting redis"
	@docker inspect kubechat-redis > /dev/null 2>&1 || docker run -d --name kubechat-redis -p 6379:6379 redis:latest
	@docker start kubechat-redis

run-postgres:
	@echo "Starting postgres"
	@docker inspect kubechat-postgres > /dev/null 2>&1 || docker run -d --name kubechat-postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres
	@docker start kubechat-postgres

run-qdrant:
	@echo "Starting qdrant"
	@docker inspect kubechat-qdrant > /dev/null 2>&1 || docker run -d --name kubechat-qdrant -p 6333:6333 qdrant/qdrant
	@docker start kubechat-qdrant

run-es:
	@echo "Starting elasticsearch"
	@docker inspect kubechat-es > /dev/null 2>&1 || docker run -d --name kubechat-es -p 9200:9200 apecloud/elasticsearch:8.8.2
	@docker start kubechat-es

run-db: run-redis run-postgres run-qdrant run-es

connect-metadb:
	@docker exec -it kubechat-postgres psql -p 5432 -U postgres

clean:
	@echo "Removing db.sqlite3"
	@/bin/rm -f db.sqlite3
	@echo "Removing container kubechat-postgres"
	@docker rm -fv kubechat-postgres > /dev/null 2>&1 || true
	@echo "Removing container kubechat-redis"
	@docker rm -fv kubechat-redis > /dev/null 2>&1 || true
	@echo "Removing container kubechat-qdrant"
	@docker rm -fv kubechat-qdrant > /dev/null 2>&1 || true
	@echo "Removing container kubechat-es"
	@docker rm -fv kubechat-es > /dev/null 2>&1 || true

frontend.%:
	if cd $(FRONTEND_REPO_DIR) > /dev/null 2>&1; then \
		cd $(FRONTEND_REPO_DIR) && rm .env && git pull origin $(FRONTEND_BRANCH) && git checkout $(FRONTEND_BRANCH); \
	else \
		git clone https://github.com/apecloud/KubeChat-FrontEnd.git $(FRONTEND_REPO_DIR); \
	fi
	cp .env.$@ $(FRONTEND_REPO_DIR)/.env
	mkdir -p /tmp/kubechat-static-files/
	mkdir -p static/web/
	cd $(FRONTEND_REPO_DIR) && yarn install && yarn build
	cp -r /tmp/kubechat-static-files/* static/web/
	if [ -f "static/web/index.html" ]; then \
  		cp static/web/index.html kubechat/templates/404.html; \
 	fi

run-backend: migrate
	python manage.py collectstatic --noinput
	uvicorn config.asgi:application --host 0.0.0.0 --reload --reload-include '*.html'

compose-up: migrate
	docker-compose -f compose.yml up -d

compose-down:
	docker-compose -f compose.yml down

compose-logs:
	docker-compose -f compose.yml logs -f

format:
	poetry run ruff --preview --fix .

lint:
	poetry run ruff --preview .

static-check:
	poetry run mypy .

test:
	echo "mock"

celery:
	celery -A config.celery worker -B -l INFO

flower:
	celery -A config.celery flower --conf/flowerconfig.py

poetry-lock-no-update:
	poetry lock --no-update
