#!/bin/bash

gunicorn main:app --config ./core/gunicorn_conf.py
