VERSION ?= v0.1.1
LLMSERVER_VERSION ?= v0.1.1
BUILDX_PLATFORM ?= linux/amd64
BUILDX_ARGS ?= --sbom=false --provenance=false
REGISTRY ?= registry.cn-hangzhou.aliyuncs.com

init:
	cp envs/.env.template .env
	cp envs/.env.frontend.template .env.frontend

build-requirements:
	sh scripts/export-requirements.sh

image: build-requirements update-frontend
	docker buildx build -t $(REGISTRY)/apecloud/kubechat:$(VERSION) --platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) --push -f ./Dockerfile  .

llm-server-image: build-requirements
	docker buildx build -t $(REGISTRY)/apecloud/kubechat-llmserver:$(LLMSERVER_VERSION) --platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) --push -f ./Dockerfile-llmserver  .

diff:
	@python manage.py diffsettings

migrate:
	@python manage.py makemigrations
	@python manage.py migrate

clean:
	/bin/rm -f db.sqlite3

update-frontend:
	git submodule update --init --recursive --remote
	cp envs/.env.frontend.template KubeChat-FrontEnd/.env
	cd KubeChat-FrontEnd && yarn install && yarn build

run-backend: migrate
	python manage.py collectstatic --noinput
	if [ -f "static/web/index.html" ]; then \
  		cp static/web/index.html kubechat/templates/404.html; \
  	fi
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
