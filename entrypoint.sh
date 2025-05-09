#!/bin/sh
set -e

uv run manage.py migrate

exec uv run $@