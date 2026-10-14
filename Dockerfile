FROM ubuntu:stonking

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory and copy project files
WORKDIR /app

# Install Python version specified in .python-version
COPY .python-version ./
RUN uv python install

# Copy project metadata and install dependencies
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-install-project

# Copy source code and install app
COPY src ./src
RUN uv sync --locked

# Build static assets
RUN uv run camille collectstatic --noinput

# Set entrypoint
COPY entrypoint.sh /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Run the development server
CMD ["camille", "runserver", "0.0.0.0:8000"]