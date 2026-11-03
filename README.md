# Camille

An AI-powered assistant (chatbot) for [Mattermost](https://mattermost.com/) and [Zulip](https://zulip.com/). Camille connects to a Mattermost instance via WebSocket and/or to a Zulip server via its event queue API, listens to conversations, and responds using large language models.

## Tech Stack

- **Language:** Python 3.14
- **Framework:** Django 5.2 (ASGI via Daphne/Channels)
- **AI:** pydantic-ai with support for Anthropic, AWS Bedrock, Google, Mistral
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
  zulip.py             # Zulip event queue/API client
  views.py             # Web views
  ai/
    agent.py           # Per-user agent factory
    models.py          # AI model definitions
    image_models.py    # Image generation model definitions
    deps.py            # AI dependency injection
    capabilities/      # Pluggable AI capabilities (memory, personality, tools)
  management/commands/
    mattermost.py      # Management command to run the Mattermost bot
    zulip.py           # Management command to run the Zulip bot
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
| `ZULIP_SITE` | URL of the Zulip server |
| `ZULIP_EMAIL` | Email address of the Zulip bot |
| `ZULIP_API_KEY` | API key of the Zulip bot |
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

### Zulip Bot

```bash
uv run camille zulip
```

1. In Zulip, create a bot (*Personal settings → Bots → Add a new bot*, type "Generic bot").
2. Set `ZULIP_SITE`, `ZULIP_EMAIL` (the bot's email) and `ZULIP_API_KEY` (the bot's API key).
3. Subscribe the bot to the channels where it should answer. It answers when mentioned (`@**Camille**`) in a channel, and to every direct message.

Each channel topic is a separate conversation. In direct messages, send `!/reset` to start a new conversation, and `!/help` for the other commands.

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

Copyright (C) Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>

This program is free software: you can redistribute it and/or modify it under the terms of the [GNU Affero General Public License](LICENSE) as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See [LICENSE](LICENSE) for the full text.
