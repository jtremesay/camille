import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from camille.main import amain, main


class TestMain:
    """Test main module async functions."""

    def test_amain_success(self):
        """Test successful amain execution."""

        async def run_test():
            # Mock the MattermostClient
            mock_user = MagicMock()
            mock_user.username = "testuser"
            mock_user.first_name = "Test"
            mock_user.last_name = "User"

            mock_client = AsyncMock()
            mock_client.users.get_me.return_value = mock_user

            with patch("camille.main.MattermostClient") as mock_client_class:
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client_class.return_value.__aexit__.return_value = None

                # Should not raise
                await amain()

                # Verify client was instantiated and used
                mock_client.users.get_me.assert_called_once()

        asyncio.run(run_test())

    def test_amain_uses_settings(self):
        """Test that amain uses settings for base_url and token."""

        async def run_test():
            mock_user = MagicMock()
            mock_client = AsyncMock()
            mock_client.users.get_me.return_value = mock_user

            with (
                patch("camille.main.settings") as mock_settings,
                patch("camille.main.MattermostClient") as mock_client_class,
            ):
                mock_settings.MATTERMOST_URL = "https://test.com"
                mock_settings.MATTERMOST_TOKEN = "test_token"
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client_class.return_value.__aexit__.return_value = None

                await amain()

                # Verify settings were used
                mock_client_class.assert_called_once_with(
                    base_url="https://test.com", token="test_token"
                )

        asyncio.run(run_test())

    def test_amain_handles_exception(self):
        """Test that amain handles exceptions gracefully."""

        async def run_test():
            mock_client = AsyncMock()
            mock_client.users.get_me.side_effect = Exception("Connection failed")

            with patch("camille.main.MattermostClient") as mock_client_class:
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client_class.return_value.__aexit__.return_value = None

                # Should raise the exception
                with pytest.raises(Exception, match="Connection failed"):
                    await amain()

        asyncio.run(run_test())

    def test_main_calls_run(self):
        """Test that main() calls asyncio.run()."""
        with patch("camille.main.run") as mock_run:
            main()

            # Verify run was called once
            mock_run.assert_called_once()
