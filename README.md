# Camille

An AI-powered assistant (chatbot) for [Mattermost](https://mattermost.com/). Camille connects to a Mattermost instance via WebSocket, listens to conversations, and responds using large language models.

## Tech Stack

- **Language:** Python 3.14
- **Framework:** Django 5.2 (ASGI via Daphne/Channels)
- **AI:** pydantic-ai with support for Anthropic, AWS Bedrock, Google, Mistral, and OpenRouter
- **Database:** PostgreSQL (production), SQLite (development)
- **Containerization:** Docker, Docker Compose / Swarm
- **CI/CD:** GitHub Actions
- **Package manager:** uv

## Project Structure

```
src/camille/
  settings.py          # Django settings (environment-driven)
  models.py            # Django models (credentials, conversations, agent config)
  mattermost.py        # Mattermost WebSocket/API client
  views.py             # Web views
  ai/
    models.py          # AI model definitions
    deps.py            # AI dependency injection
    capabilities/      # Pluggable AI capabilities (memory, personality, tools)
  management/commands/
    mattermost.py      # Management command to run the bot
```

## Setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/)

### Development

```bash
cp .env.sample .env       # Configure environment variables
uv sync                   # Install dependencies
uv run camille migrate    # Run database migrations
```

### Environment Variables

| Variable | Description |
|---|---|
| `MATTERMOST_BASE_URL` | URL of the Mattermost instance |
| `MATTERMOST_API_TOKEN` | Bot API token for Mattermost |
| `LOGFIRE_TOKEN` | Token for Pydantic Logfire observability |
| `LOGFIRE_ENVIRONMENT` | Logfire environment name |
| `SECRET_KEY` | Django secret key |
| `SALT_KEY` | Salt key for encrypted fields |
| `DEBUG` | Enable Django debug mode |
| `DATABASE_URL` | Database connection string (defaults to SQLite) |

## Running

### Development Server

```bash
uv run camille runserver
```

### Mattermost Bot

```bash
uv run camille mattermost
```

## Testing

```bash
uv sync --group test
uv run pytest tests/
```

## Docker

### Build

```bash
make image
```

### Production Deployment

The production stack is defined in `compose.yml` and runs:

- PostgreSQL 18
- Web service (Daphne on port 8000 behind Traefik)
- Mattermost bot service

Deployment is automated via GitHub Actions on push to the `v6` branch: tests run, a Docker image is built and pushed to Docker Hub, then deployed to Docker Swarm.

## License

See the project repository for license information.
