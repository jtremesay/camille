# Camille, an AI assistant for MatterMost

Previously known as Laura.

## Configuration

Camille search for its config in the following order:
- environment variables
- docker secrets file
- the project's settings.py
- a default value if available
- raise an error

### GEMINI_API_KEY

The API key for Gogle Gemini API. Get a key [here](https://aistudio.google.com/apikey).

Default: no default. You MUST provide a value


### MATTERMOST_HOST

The mattermost host.

Default: no default. You MUST provide a value


### MATTERMOST_API_TOKEN

The mattermost API token.

Default: no default. You MUST provide a value


## Run

```shell
# Install requirements
pip install -r requirements.txt

# Run the xmpp handler
python -m camille
```