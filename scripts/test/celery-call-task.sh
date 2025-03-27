#!/usr/bin/env bash

celery -A celery -A config.celery call deeprag.tasks.index.add_index_for_local_document --args='["1"]'