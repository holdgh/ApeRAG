#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset


python manage.py migrate

# store kbcli documents to vector db
python store_doc2vectordb.py

if [ -f "static/web/index.html" ]; then
  cp static/web/index.html kubechat/templates/404.html
fi

# uvicorn supports multiple workers
exec uvicorn config.asgi:application --host 0.0.0.0 --log-config uvicorn-log-config.yaml

#exec daphne config.asgi:application -b 0.0.0.0
