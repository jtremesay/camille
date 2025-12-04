# Camille, an AI assistant for MatterMost

## Configuration

Camille search for its config in the following order:
- docker secrets file
- environment variables
- a default value if available
- raise an error

### MATTERMOST_HOST

The Mattermost host.

Default: no default. You MUST provide a value

### MATTERMOST_ACCESS_TOKEN

The Mattermost access token.

Default: no default. You MUST provide a value

### TAVILY_API_KEY

The Tavily API key.

Default: no default. Optional. If not provided, Camille will not use Tavily features.

## Run

```shell
# Install requirements
uv sync

# Run Camille
uv run main.py
```