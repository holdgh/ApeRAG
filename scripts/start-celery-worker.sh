#!/bin/bash

set -o errexit
set -o nounset


exec celery -A config.celery worker -l INFO --concurrency 4
