# Copilot Instructions for Camille v6

## Project Overview

Camille is an AI assistant for Mattermost, built with Django. It's an AI agent that integrates with Mattermost to provide intelligent conversational capabilities using various LLM providers (Google Gemini, Mistral, AWS Bedrock Claude).

## Tech Stack

- **Framework**: Django 6.x
- **Python**: 3.13+
- **Database**: PostgreSQL (via psycopg), SQLite for development
- **Async Support**: Django Channels, Daphne (ASGI server)
- **AI Framework**: pydantic-ai with support for:
  - Google Gemini
  - Mistral
  - AWS Bedrock (Claude)
  - Tavily search integration
- **HTTP Client**: httpx with websocket support (httpx-ws)
- **Monitoring**: Logfire
- **Static Files**: WhiteNoise

## Architecture

### Core Components

1. **Django Application**: `camille/` - Main Django app
2. **Project Settings**: `proj/` - Django project configuration
3. **AI Agent Layer**: Handles LLM interactions via pydantic-ai
4. **Mattermost Integration**: WebSocket-based real-time communication
5. **Database Models**: Users, channels, threads, messages, prompts

### Key Patterns

- **Async-first**: Use async Django ORM (`aget`, `aupdate_or_create`, `asave`, etc.)
- **Event-driven**: WebSocket events from Mattermost drive agent interactions
- **Tool-based architecture**: AI agents have access to toolsets for various capabilities
- **User-configurable**: Each user can configure their own model and personality prompts

## Code Style & Conventions

### General Python
- Use Python 3.13+ features
- Type hints are required (use `typing` module)
- Prefer async/await for I/O operations
- Use f-strings for string formatting
- Follow PEP 8 style guide

### Django Specific
- Always use async ORM methods when in async context
- Use `aclose_old_connections()` in long-running async tasks
- Model fields should have explicit types
- Use Django's built-in validators

### AI/Agent Code
- All agent functions should be properly typed with `RunContext[Dependency]`
- Tools should have clear docstrings explaining their purpose and args
- Use `FunctionToolset` for organizing related tools
- Always handle agent errors gracefully with user-friendly messages

### Error Handling
- Catch specific exceptions, not bare `except:`
- Log errors with logfire: `logfire.exception()`
- Return user-friendly error messages to Mattermost
- Always wrap async database operations in try/except

## Important Considerations

### Mattermost Integration
- Never respond to messages from the bot itself (check `sender_id == self.me.id`)
- Ignore non-text posts (system messages, etc.)
- Only respond in DMs or when mentioned in channels
- Handle commands starting with `!/`
- Support file attachments with proper MIME type handling

### Database
- Use `aupdate_or_create` for idempotent updates
- Always check if user has a model configured before processing
- Thread history management is critical for context
- Close old connections in event handlers

### AI Agent Best Practices
- System prompts should be dynamic and user-configurable
- Support multiple LLM providers (Google, Mistral, Bedrock)
- Use binary content for file attachments
- Stream responses when using `agent.iter()`
- Maintain conversation history per thread

### Tool Development
- Tools should be composable and focused on single responsibility
- Use dependency injection via `RunContext[Dependency]`
- Tools can access: current user, sender, channel, users in channel
- Common toolsets: model management, prompt management, notes, URL fetching, web search (Tavily)

## Configuration

The application expects these environment variables:
- `GEMINI_API_KEY`: Google Gemini API key
- `MATTERMOST_HOST`: Mattermost server URL
- `MATTERMOST_API_TOKEN`: Bot API token
- `TAVILY_API_KEY`: Optional, for web search capabilities
- Database configuration via `dj-database-url`

## File Organization

```
camille/
  ai/           # AI agent core (models, tools, prompts)
  mattermost/   # Mattermost integration (client, agent, commands)
  management/   # Django management commands
  migrations/   # Database migrations
  models.py     # Django models (User, Channel, Thread, etc.)
  
proj/
  settings.py   # Django settings
  urls.py       # URL configuration
  asgi.py       # ASGI application
```

## Testing
- Always test async functions with proper async context
- Mock Mattermost API calls in tests
- Test both successful and error paths
- Verify database state after operations

## Common Tasks

### Adding a New Tool
1. Create async function in appropriate toolset file
2. Add type hints including `RunContext[Dependency]`
3. Write comprehensive docstring (used by AI)
4. Add to toolset using `FunctionToolset`
5. Register toolset in agent creation

### Adding a New Model Field
1. Update model in `models.py`
2. Generate migration: `python manage.py makemigrations`
3. Update any serialization/deserialization logic
4. Update Mattermost sync if needed

### Debugging Agent Issues
1. Check logfire output for errors
2. Verify user has model configured
3. Check message history is being maintained
4. Ensure tools are registered correctly
5. Validate dependency injection is working

## Version History Context

This is v6, a complete rewrite. Previous versions (v1-v5) exist but this is a fresh start with:
- Modern Django (6.x)
- Python 3.13+
- pydantic-ai framework
- Enhanced async support
- Better tool architecture
