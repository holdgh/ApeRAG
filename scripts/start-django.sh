#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset


python manage.py migrate

#exec uvicorn config.asgi:application --host 0.0.0.0 --reload --reload-include '*.html'
exec daphne config.asgi:application -b 0.0.0.0