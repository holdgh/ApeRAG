

diff:
	@python manage.py diffsettings

migrate:
	@python manage.py makemigrations
	@python manage.py migrate

clean:
	/bin/rm -rf kubechat/migrations/0*
	/bin/rm -f db.sqlite3

run-backend: migrate
	daphne config.asgi:application -b 0.0.0.0

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
