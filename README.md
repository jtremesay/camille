# Camille, an AI assistant

Previously known as Laura.

## Configuration

Camille search for its config in the following order:
- environment variables
- docker secrets file
- the project's settings.py
- a default value if available
- raise an error

### GOOGLE_API_KEY

The API key for Gogle Gemini api model.

Default: no default. You MUST provide a value


### CAMILLE_NAME

The name of Camille.

Default: `"Camille"`


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