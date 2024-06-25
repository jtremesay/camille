# Camille, an AI assistant

Previously known as Laura.


## Configuration

Camille search for its config in the following order:
- environment variables
- docker secrets file
- the project's settings.py
- a default value if available
- raise an error

### CAMILLE_NAME

The name of Camille.

Default: `"Cmille"`

### CAMILLE_LLM_MODEL

The LLM model used by Camille.

Default: `"gemini-1.5-pro"`

### CAMILLE_LLM_MESSAGES_COUNT

Conversation history window size. 

Default: `128`

### CAMILLE_XMPP_JID

The identifier used to connect to XMPP

Default: not default. You MUST provide a value

### CAMILLE_XMPP_PASSWORD

The password used to connect to XMPP

Default: not default. You MUST provide a value

### CAMILLE_XMPP_CHANNELS

A list of channels to join

If passed by envvar, you need to provide a comma separated list of jid. E.g: `CAMILLE_XMPP_CHANNELS='channel@server,channel2@server' ./manage.py xmpp`

Default: `[]`
