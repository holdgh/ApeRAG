

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
