import pytest


class TestSettings:
    """Test settings module environment variable loading."""

    def test_settings_load_valid_env(self, monkeypatch):
        """Test that settings loads environment variables correctly."""
        monkeypatch.setenv("CAMILLE_MATTERMOST_URL", "https://mattermost.example.com")
        monkeypatch.setenv("CAMILLE_MATTERMOST_TOKEN", "test_token_123")

        # Reimport to get fresh environment
        import importlib

        import camille.settings as settings

        importlib.reload(settings)

        assert settings.MATTERMOST_URL == "https://mattermost.example.com"
        assert settings.MATTERMOST_TOKEN == "test_token_123"

    def test_settings_missing_url(self, monkeypatch):
        """Test that KeyError is raised when MATTERMOST_URL is missing."""
        monkeypatch.delenv("CAMILLE_MATTERMOST_URL", raising=False)
        monkeypatch.setenv("CAMILLE_MATTERMOST_TOKEN", "test_token")

        import importlib

        import camille.settings as settings

        with pytest.raises(KeyError, match="CAMILLE_MATTERMOST_URL"):
            importlib.reload(settings)

    def test_settings_missing_token(self, monkeypatch):
        """Test that KeyError is raised when MATTERMOST_TOKEN is missing."""
        monkeypatch.setenv("CAMILLE_MATTERMOST_URL", "https://mattermost.example.com")
        monkeypatch.delenv("CAMILLE_MATTERMOST_TOKEN", raising=False)

        import importlib

        import camille.settings as settings

        with pytest.raises(KeyError, match="CAMILLE_MATTERMOST_TOKEN"):
            importlib.reload(settings)

    def test_settings_missing_both(self, monkeypatch):
        """Test that KeyError is raised when both env vars are missing."""
        monkeypatch.delenv("CAMILLE_MATTERMOST_URL", raising=False)
        monkeypatch.delenv("CAMILLE_MATTERMOST_TOKEN", raising=False)

        import importlib

        import camille.settings as settings

        with pytest.raises(KeyError):
            importlib.reload(settings)
