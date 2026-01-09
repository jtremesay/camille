from asyncio import run
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from mattermost.client import MattermostClient


class TestMattermostClientContextManager(IsolatedAsyncioTestCase):
    def test_context_manager_enter(self):
        """Test entering context manager."""

        async def run_test():
            client = MattermostClient(
                base_url="https://mattermost.example.com", token="token"
            )

            # Mock the underlying http_client context manager
            client.http_client.__aenter__ = AsyncMock(return_value=client.http_client)

            result = await client.__aenter__()

            self.assertEqual(result, client)
            client.http_client.__aenter__.assert_called_once()

        run(run_test())

    def test_context_manager_exit(self):
        """Test exiting context manager."""

        async def run_test():
            client = MattermostClient(
                base_url="https://mattermost.example.com", token="token"
            )

            # Mock the underlying http_client context manager
            client.http_client.__aexit__ = AsyncMock(return_value=None)

            await client.__aexit__(None, None, None)

            client.http_client.__aexit__.assert_called_once_with(None, None, None)

        run(run_test())

    def test_context_manager_full_flow(self):
        """Test full async context manager flow."""

        async def run_test():
            with patch("mattermost.client.HttpClient") as mock_http_class:
                mock_http_instance = AsyncMock()
                mock_http_class.return_value = mock_http_instance

                client = MattermostClient(
                    base_url="https://mattermost.example.com", token="token"
                )

                async with client as ctx:
                    self.assertEqual(ctx, client)

                mock_http_instance.__aenter__.assert_called_once()
                mock_http_instance.__aexit__.assert_called_once()

        run(run_test())

    async def test_get_method(self):
        """Test the GET method of MattermostClient."""
        client = MattermostClient(
            base_url="https://mattermost.example.com", token="token"
        )

        mock_response = Mock()
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status = Mock()

        client.http_client.get = AsyncMock(return_value=mock_response)

        response = await client.get("/test-endpoint", params={"param1": "value1"})

        client.http_client.get.assert_called_once_with(
            "/test-endpoint", params={"param1": "value1"}
        )
        mock_response.raise_for_status.assert_called_once()
        self.assertEqual(response, {"key": "value"})


class TestMattermostClient(IsolatedAsyncioTestCase):
    async def test_get_user_me(self):
        """Test getting current user info."""
        client = MattermostClient(
            base_url="https://mattermost.example.com", token="token"
        )

        mock_response = {
            "id": "current_user",
            "create_at": 1625079600000,
            "update_at": 1625079600000,
            "delete_at": 0,
            "username": "current",
            "nickname": "Current",
            "first_name": "Current",
            "last_name": "User",
        }

        client.get = AsyncMock(return_value=mock_response)

        user = await client.users.get_me()
        client.get.assert_called_once_with("/users/me")
        self.assertEqual(user.username, "current")
        self.assertEqual(user.id, "current_user")
