# Camille v6

🤖 AI Assistant for Mattermost

Camille is a powerful AI assistant that integrates with Mattermost to provide intelligent conversational capabilities using multiple LLM providers (Google Gemini, Mistral, AWS Bedrock Claude).

## Tech Stack

- **Framework**: Django 6.x
- **Python**: 3.13+
- **Database**: PostgreSQL (production), SQLite (development)
- **AI Framework**: pydantic-ai
- **Frontend**: Bootstrap 5
- **Package Managers**: uv (Python), bun (JavaScript)

## Features

- 🤖 Multiple AI Providers (Google Gemini, Mistral, AWS Bedrock Claude)
- 🔐 Secure credential management
- 💬 Mattermost integration via WebSocket
- 🔧 Extensible tool-based architecture
- 👤 User-configurable models and personalities

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [bun](https://bun.sh/) (JavaScript runtime & package manager)
- PostgreSQL (optional, for production)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/jtremesay/camille.git
   cd camille_v6
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Install JavaScript dependencies and build Bootstrap**
   ```bash
   bun install
   bun run build:bootstrap
   ```

4. **Run database migrations**
   ```bash
   uv run manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   uv run manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   uv run manage.py runserver
   ```

7. **Access the application**
   
   Open your browser and navigate to: `http://localhost:8000`