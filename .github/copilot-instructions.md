# Copilot Instructions for Camille

## Project Overview

Camille is an AI-powered chatbot for Mattermost, built with Django 6.0 (ASGI) and pydantic-ai. It connects via WebSocket, listens to conversations, and responds using LLMs (Anthropic, AWS Bedrock, Google, Mistral, OpenRouter).

## Tech Stack

- Python 3.14, Django 6.0, Daphne (ASGI)
- pydantic-ai-slim for LLM integration
- httpx for HTTP/WebSocket communication
- PostgreSQL (production), SQLite (development)
- uv for package management
- Docker for containerization

## Project Layout

- `src/camille/` - Main Django application (single-app project)
- `src/camille/settings.py` - Environment-driven Django settings
- `src/camille/models.py` - Django models (credentials, agent config, conversations)
- `src/camille/mattermost.py` - Mattermost WebSocket/API client
- `src/camille/ai/` - AI layer (models, dependencies, capabilities)
- `src/camille/ai/capabilities/` - Pluggable AI capabilities (memory, personality, tools)
- `src/camille/management/commands/mattermost.py` - Bot management command
- `tests/` - Test suite

## Conventions

- Entry point: `camille` CLI via `src/camille/manage.py`
- Configuration is environment-driven (`.env` file, Docker secrets)
- Sensitive credentials are stored encrypted using `django-fernet-encrypted-fields`
- ASGI throughout; use async patterns where appropriate
- Tests use pytest with pytest-django and pytest-asyncio (`asyncio_mode = "auto"`)
- Linting with Ruff

## Commands

- `uv sync` - Install dependencies
- `uv run camille migrate` - Run migrations
- `uv run camille runserver` - Start dev server
- `uv run camille mattermost` - Start the Mattermost bot
- `uv run pytest tests/` - Run tests with coverage
- `make image` - Build Docker image

## Guidelines

- Follow existing code style and patterns in the codebase
- Use type hints consistently
- Keep AI capabilities modular (one file per capability in `ai/capabilities/`)
- Use `environ` for configuration; never hardcode secrets
- Write async code when interacting with Mattermost or LLM APIs
- Use Django models for persistent state; encrypted fields for credentials
- Test with pytest-django and pytest-asyncio
