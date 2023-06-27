

diff:
	@python manage.py diffsettings

llmserver:
	@python server/llmserver.py

migrate:
	@python manage.py makemigrations
	@python manage.py migrate

clean:
	/bin/rm -rf kubechat/migrations/0*
	/bin/rm -f db.sqlite3

run-backend: migrate
	uvicorn config.asgi:application --host 0.0.0.0 --reload

run-frontend:
	cd frontend && yarn dev

