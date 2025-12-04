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
COPY main.py ./

# Define entrypoint
COPY entrypoint.sh ./
ENTRYPOINT [ "/app/entrypoint.sh" ]

# Define default command
CMD ["main.py"]