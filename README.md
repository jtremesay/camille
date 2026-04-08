# Camille, an AI assistant for MatterMost

## Configuration

Camille search for its config in the following order:
- docker secrets file
- environment variables
- a default value if available
- raise an error

### MATTERMOST_BASE_URL

The mattermost base url.

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