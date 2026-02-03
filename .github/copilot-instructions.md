# Copilot Instructions for Camille v6

## Project Overview

Camille v6 is an AI assistant built with Django and pydantic-ai. It provides intelligent conversational capabilities using multiple LLM providers (Google Gemini, Mistral, AWS Bedrock Claude). The project includes:
- A web interface for secure credential management
- AI agent framework with extensible tool-based architecture
- Planned integrations with chat platforms (Mattermost, Slack, etc.)

Currently in active development, with the web interface for credential management operational and chat platform integrations on the roadmap.

## Tech Stack

- **Framework**: Django 6.x
- **Python**: 3.13+
- **Database**: PostgreSQL (production), SQLite (development)
- **AI Framework**: pydantic-ai (for agent capabilities)
- **Frontend**: Bootstrap 5
- **Package Managers**: uv (Python), bun (JavaScript)
- **Static Files**: Django's built-in static file handling
- **Planned Integrations**: Mattermost, Slack (WebSocket/API-based)

## Architecture

### Core Components

1. **Django Application**: `camille/` - Main Django app with models, views, templates
2. **Project Settings**: `proj/` - Django project configuration
3. **Database Models**: Profile, BaseCredentials, ApiKeyCredentials, AwsBedrockCredentials, GoogleGlaCredentials, MistralCredentials, UserCredentials
4. **Web Interface**: Bootstrap 5-based UI for credential management
5. **AI Agent Layer**: pydantic-ai based agent framework (planned/in development)
6. **Chat Integrations**: Platform connectors for Mattermost, Slack, etc. (planned)
7. **Authentication**: Django's built-in authentication with custom profile extension

### Key Patterns

- **Class-Based Views**: Using Django's generic views (ListView, CreateView, UpdateView, DeleteView)
- **Model Inheritance**: Credentials use Django's multi-table inheritance
- **User Profiles**: Auto-created profile extension using signals
- **Authentication**: Login required for all credential management pages
- **Tool-Based AI**: Extensible tool architecture for AI agent capabilities (planned)
- **Multi-Platform**: Support for multiple chat platforms through unified interface (planned)

## Code Style & Conventions

### General Python
- Use Python 3.13+ features
- Type hints are encouraged
- Use f-strings for string formatting
- Follow PEP 8 style guide

### Django Specific
- Use class-based views for CRUD operations
- Model fields should have explicit types
- Use Django's built-in validators
- Leverage Django's generic views (CreateView, UpdateView, DeleteView, ListView)
- Use `LoginRequiredMixin` for views requiring authentication
- Follow Django's URL naming conventions

### Templates
- Use Bootstrap 5 components consistently
- Extend from `base.html` template
- Keep templates organized by feature in subdirectories
- Use Django template inheritance and includes

### Forms
- Use Django's model forms for creating and editing credentials
- Include proper form validation
- Display user-friendly error messages

### AI/Agent Code (When Implementing)
- Use pydantic-ai for agent framework
- Type hints required for agent functions and tools
- Tools should have clear docstrings (used by AI for understanding)
- Handle agent errors gracefully with user-friendly messages
- Support multiple LLM providers through credential system

## Important Considerations

### Credential Security
- Never log or display API keys in plain text
- Use environment variables for sensitive configuration
- Ensure credentials are only accessible by their owner
- Follow Django security best practices for credential storage

### User Experience
- Provide clear feedback on credential operations (create, update, delete)
- Use Bootstrap alerts for success/error messages
- Implement proper form validation with user-friendly error messages
- Ensure responsive design works on mobile devices

### Database
- Use Django's ORM for all database operations
- Profile is auto-created via signals when a user is created
- UserCredentials links a user's profile to their credentials
- Support multiple credentials per user for the same provider

### AI Agent Integration (Planned)
- Agent will use user-configured credentials to access LLM providers
- Support for tool-based extensibility
- User-configurable personalities and system prompts
- Conversation history management per chat thread

### Chat Platform Integration (Planned)
- Mattermost: WebSocket-based real-time communication (in roadmap)
- Slack: API-based integration (in roadmap)
- Other platforms: Extensible connector architecture
- Handle platform-specific message formats and events

## Configuration

The application uses Django's standard configuration:
- `SECRET_KEY`: Django secret key (should be changed in production)
- `DEBUG`: Set to False in production
- `ALLOWED_HOSTS`: Configure for production deployment
- Database: SQLite for development, PostgreSQL recommended for production
- Static files served via Django's built-in handling
- Authentication URLs: LOGIN_URL="/login/", LOGIN_REDIRECT_URL="/home/", LOGOUT_REDIRECT_URL="/"

## File Organization

```
camille/
  migrations/       # Database migrations
  static/           # Static files (CSS, Bootstrap)
    camille/        # App-specific static files
    third-party/    # Third-party libraries (Bootstrap)
  templates/        # Django templates
    base.html       # Base template
    camille/        # App-specific templates
    registration/   # Authentication templates
  models.py         # Django models (Profile, Credentials)
  views.py          # Class-based views
  urls.py           # URL routing
  admin.py          # Django admin configuration
  
proj/
  settings.py       # Django settings
  urls.py           # Root URL configuration
  wsgi.py           # WSGI application
  asgi.py           # ASGI application (for future use)
```

## Testing
- Write tests for models, views, and forms
- Test authentication and authorization
- Verify credential CRUD operations
- Test user profile auto-creation

## Common Tasks

### Adding a New Credential Type
1. Create new model inheriting from `ApiKeyCredentials` in [models.py](camille/models.py)
2. Generate migration: `python manage.py makemigrations`
3. Create views (CreateView, UpdateView, DeleteView) in [views.py](camille/views.py)
4. Add URL patterns in [urls.py](camille/urls.py)
5. Update templates for the new credential type
6. Update credentials list view to include the new type

### Adding a New Model Field
1. Update model in [models.py](camille/models.py)
2. Generate migration: `python manage.py makemigrations`
3. Run migration: `python manage.py migrate`
4. Update forms and views as needed
5. Update templates to display the new field

### Customizing the UI
1. Edit Bootstrap 5 templates in `camille/templates/`
2. Add custom CSS in `camille/static/camille/style.css`
3. Use Bootstrap components for consistency
4. Test responsive design on mobile devices

## Version History Context

This is v6, a complete rewrite. Previous versions (v1-v5) exist but this is a fresh start with:
- Modern Django (6.x)
- Python 3.13+
- pydantic-ai framework for AI agent capabilities
- Bootstrap 5 web UI for credential management
- Extensible architecture for multiple chat platforms
- Better security practices
- Focus on modular, scalable design

## Current Development Status

**Completed:**
- ✅ Web interface for credential management
- ✅ User authentication and profiles
- ✅ Multi-provider credential storage (Google, Mistral, AWS Bedrock)
- ✅ Bootstrap 5 responsive UI

**In Progress/Planned:**
- 🚧 Mattermost integration (in roadmap)
- 🚧 Slack integration (in roadmap)
- 🚧 pydantic-ai agent framework integration
- 🚧 Tool-based extensibility system
- 🚧 User-configurable AI personalities
