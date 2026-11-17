FROM ubuntu:latest

# Install GCC and other dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

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
RUN uv sync --no-install-project

# Remove build dependencies
RUN apt-get remove -y build-essential && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy source
COPY entrypoint.sh README.md ./
COPY src/ src/

# Install project
RUN uv sync
ENV UV_NO_SYNC=1

# Collect static files
RUN \
    SECRET_KEY="empty" \
    SALT_KEY="empty" \
    uv run camille collectstatic --noinput

# Expose port and run
ENTRYPOINT [ "/app/entrypoint.sh" ]
EXPOSE 8000
CMD ["daphne", "-p", "8000", "-b", "0.0.0.0", "camille.asgi:application"]