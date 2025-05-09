#!/bin/bash

uv run manage.py migrate

exec uv run $@