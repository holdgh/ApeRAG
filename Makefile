

diff:
	@python manage.py diffsettings

llmserver:
	@python server/llmserver.py

webserver:
	@python manage.py runserver

migrate: clean
	@python manage.py makemigrations
	@python manage.py migrate

clean:
	/bin/rm -rf kubechat/migrations/0*
	/bin/rm -f db.sqlite3


run:
	exec uvicorn config.asgi:application --host 0.0.0.0 --reload --reload-include '*.html' --reload-exclude './chat_all_the_docs/media/*'