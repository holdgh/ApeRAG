VERSION ?= v1.0.0
BUILDX_PLATFORM ?= linux/amd64,linux/arm64
BUILDX_ARGS ?= --sbom=false --provenance=false

build:
	docker buildx build -t apecloud/kubechat:$(VERSION) --platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) --push -f ./Dockerfile  .


diff:
	@python manage.py diffsettings

migrate:
	@python manage.py makemigrations
	@python manage.py migrate

clean:
	/bin/rm -rf kubechat/migrations/0*
	/bin/rm -f db.sqlite3

run-backend: migrate
	python scripts/store_doc2vectordb.py
	python manage.py collectstatic --noinput
	if [ -f "static/web/index.html" ]; then \
  		cp static/web/index.html kubechat/templates/404.html; \
  	fi
	uvicorn config.asgi:application --host 0.0.0.0 --reload --reload-include '*.html'

run-frontend:
	cd frontend && yarn dev

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
