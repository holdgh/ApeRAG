#!/usr/bin/env bash

poetry export --without-urls -o requirements.txt
poetry export --with=llmserver --without-urls -o requirements-llmserver.txt
