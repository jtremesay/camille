FROM alpine:latest AS base

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
ENV UV_COMPILE_BYTECODE=1
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project

# Copy source
COPY README.md ./
COPY src src
RUN uv sync
ENV UV_NO_SYNC=1

# Define entrypoint
COPY entrypoint.sh ./
ENTRYPOINT [ "/app/entrypoint.sh" ]

# Define default command
CMD ["-m", "camille"]