#!/bin/sh
set -e

uv run camille migrate

exec uv run $@