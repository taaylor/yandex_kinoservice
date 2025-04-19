#!/bin/bash

alembic upgrade head
gunicorn main:app --config ./core/gunicorn_conf.py
