makemigrations:
    uv run camille makemigrations

migrate:
    uv run camille migrate

runserver:
    uv run camille runserver

test:
    uv run coverage run --source="src/camille" -m camille test tests
    uv run coverage report

buildimage:
    docker build -t killruana/camille .