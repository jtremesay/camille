makemigrations:
    uv run camille makemigrations

migrate:
    uv run camille migrate

runserver:
    uv run camille runserver

test:
    uv run coverage run --source="src/" -m camille test --parallel=auto camille.tests
    uv run coverage report