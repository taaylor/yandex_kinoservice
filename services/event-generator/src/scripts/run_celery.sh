#!/bin/bash
set -e

if [[ "${1}" == "celery" ]]; then
    celery --app=tasks.celery_config:celery_engine worker -l INFO
elif [[ "${1}" == "celery_beat" ]]; then
    celery --app=tasks.celery_config:celery_engine worker -l INFO -B
elif [[ "${1}" == "flower" ]]; then
    celery --app=tasks.celery_config:celery_engine flower
else
    echo "Usage: $0 {celery|celery_beat|flower}"
    exit 1
fi
