#!/bin/sh

set -e

# Run the migrations
uv run camille migrate

# Run the specified command
exec uv run "$@"