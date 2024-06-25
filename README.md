# Camille, an AI assistant

Previously known as Laura.


## Configuration

Camille search for its config in the following order:
- environment variables
- docker secrets file
- the project's settings.py
- a default value if available
- raise an error

### OPENAI_API_KEY

The API key for the LLM model.

Default: no default. You MUST provide a value

### OPENAI_BASE_URL

The API url for the LLM model.

Default: no default. You MUST provide a value


### CAMILLE_NAME

The name of Camille.

Default: `"Cmille"`

### CAMILLE_LLM_MODEL

The LLM model used by Camille.

Default: `"gemini-1.5-pro"`

### CAMILLE_LLM_MESSAGES_COUNT

Conversation history window size. 

Default: `64`

### CAMILLE_XMPP_JID

The identifier used to connect to XMPP

Default: no default. You MUST provide a value

### CAMILLE_XMPP_PASSWORD

The password used to connect to XMPP

Default: no default. You MUST provide a value

### CAMILLE_XMPP_CHANNELS

A list of channels to join

If passed by envvar, you need to provide a comma separated list of jid. E.g: `CAMILLE_XMPP_CHANNELS='channel@server,channel2@server' ./manage.py xmpp`

Default: `[]`


## Run

```shell
# Install requirements
pip install -r requirements.txt

# Run the xmpp handler
./manage.py xmpp
```