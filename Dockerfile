FROM python:3.13
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync
COPY entrypoint.sh manage.py ./
COPY proj/ proj/
COPY camille/ camille/
RUN \
    SECRET_KEY="empty" \
    uv run manage.py collectstatic --noinput
EXPOSE 8000
ENTRYPOINT [ "/app/entrypoint.sh" ]
CMD ["daphne", "-p", "8000", "-b", "0.0.0.0", "proj.asgi:application"]