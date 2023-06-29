

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
	daphne config.asgi:application -b 0.0.0.0

run-frontend:
	cd frontend && yarn dev

