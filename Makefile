VERSION ?= v0.1.2
VERSION_FILE ?= version/__init__.py
LLMSERVER_VERSION ?= v0.1.1
BUILDX_PLATFORM ?= linux/amd64
BUILDX_ARGS ?= --sbom=false --provenance=false
REGISTRY ?= registry.cn-hangzhou.aliyuncs.com
FRONTEND_BRANCH ?= main

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

clean:
	/bin/rm -f db.sqlite3
	/bin/rm -f resources/db.sqlite3

git-update-frontend:
	git submodule set-branch -b $(FRONTEND_BRANCH) KubeChat-FrontEnd
	git submodule update --init --recursive --remote

frontend.%: git-update-frontend
	cp .env.$@ KubeChat-FrontEnd/.env
	cd KubeChat-FrontEnd && yarn install && yarn build
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
	poetry run black .
	poetry run ruff --select I --fix .

lint: PYTHON_FILES=.
lint_diff: PYTHON_FILES=$(shell git diff --name-only --diff-filter=d master | grep -E '\.py$$')

lint lint_diff:
	poetry run mypy $(PYTHON_FILES)
	poetry run black $(PYTHON_FILES) --check
	poetry run ruff .

test:
	echo "mock"

celery:
	celery -A config.celery worker -B -l INFO

flower:
	celery -A config.celery flower --conf/flowerconfig.py
