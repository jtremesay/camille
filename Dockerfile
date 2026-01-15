FROM alpine:latest

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Prepare app
WORKDIR /app

# Install python
COPY .python-version ./
RUN uv python install

# Install dependencies
ENV UV_FROZEN=1
ENV UV_NO_DEV=1
COPY pyproject.toml uv.lock ./
RUN uv sync
ENV UV_NO_SYNC=1

# Copy source
COPY entrypoint.sh manage.py ./
COPY proj/ proj/
COPY camille/ camille/

# Collect static files
RUN \
    SECRET_KEY="empty" \
    uv run manage.py collectstatic --noinput

# Expose port and run
ENTRYPOINT [ "/app/entrypoint.sh" ]
EXPOSE 8000
CMD ["daphne", "-p", "8000", "-b", "0.0.0.0", "proj.asgi:application"]