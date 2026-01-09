# Camille - The anarcho-communist mattermost agent

## Installation

```shell
$ git clone https://github.com/jtremesay/camille.git
$ cd camille
$ uv sync
```

## Usage

```shell
$ uv run camille
```

## Configuration

Configuration is done via environment variables.

### CAMILLE_MATTERMOST_URL

The URL of the Mattermost server. Required.

### CAMILLE_MATTERMOST_TOKEN

The personal access token for the Mattermost bot account. Required.

## Testing

```shell
$ uv run pytest
```