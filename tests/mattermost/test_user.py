import asyncio
from datetime import datetime
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from camille.mattermost import MattermostClient, MMUser, MMUserClient


class TestMMObject(TestCase):
    """Test base MMObject class."""

    def test_from_json_base_class(self):
        """Test MMObject.from_json base implementation."""
        from camille.mattermost import MMObject

        json_data = {
            "field1": "value1",
            "field2": "value2",
        }

        # This would normally fail without actual pydantic fields,
        # but we can test that it calls cls(**data)
        obj = MMObject.from_json(json_data)
        self.assertIsNotNone(obj)


class TestMMUser(TestCase):
    def test_from_json(self):
        json_data = {
            "id": "user123",
            "create_at": 1625079600000,
            "update_at": 1625079600000,
            "delete_at": 0,
            "username": "johndoe",
            "nickname": "John",
            "first_name": "John",
            "last_name": "Doe",
        }
        user = MMUser.from_json(json_data)
        self.assertEqual(user.id, "user123")
        self.assertEqual(user.username, "johndoe")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.nickname, "John")
        self.assertEqual(user.created_at.year, 2021)
        self.assertEqual(user.delete_at.year, 1970)

    def test_from_json_with_zero_timestamps(self):
        """Test MMUser creation with zero timestamps (deleted users)."""
        json_data = {
            "id": "deleted_user",
            "create_at": 1625079600000,
            "update_at": 1625079600000,
            "delete_at": 0,
            "username": "deleted",
            "nickname": "",
            "first_name": "",
            "last_name": "",
        }
        user = MMUser.from_json(json_data)
        self.assertEqual(user.delete_at.year, 1970)
        self.assertEqual(user.username, "deleted")

    def test_from_json_with_different_timestamps(self):
        """Test MMUser with different create/update timestamps."""
        json_data = {
            "id": "user456",
            "create_at": 1609459200000,  # 2021-01-01
            "update_at": 1640995200000,  # 2022-01-01
            "delete_at": 0,
            "username": "updated_user",
            "nickname": "Updated",
            "first_name": "Up",
            "last_name": "Dated",
        }
        user = MMUser.from_json(json_data)
        self.assertEqual(user.created_at.year, 2021)
        self.assertEqual(user.update_at.year, 2022)
        self.assertNotEqual(user.created_at, user.update_at)

    def test_mmuser_model_fields(self):
        """Test that MMUser has all required fields."""
        user = MMUser(
            id="test",
            created_at=datetime.now(),
            update_at=datetime.now(),
            delete_at=datetime.now(),
            username="test",
            nickname="test",
            first_name="test",
            last_name="test",
        )
        self.assertIsNotNone(user.id)
        self.assertIsNotNone(user.username)
        self.assertIsNotNone(user.created_at)


class TestMMUserClient(TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = AsyncMock(spec=MattermostClient)
        self.user_client = MMUserClient(self.mock_client)

    def test_get_me(self):
        """Test getting current user info."""
        json_data = {
            "id": "current_user",
            "create_at": 1625079600000,
            "update_at": 1625079600000,
            "delete_at": 0,
            "username": "current",
            "nickname": "Current",
            "first_name": "Current",
            "last_name": "User",
        }

        self.mock_client.get = AsyncMock(return_value=json_data)

        # Run async test
        async def run_test():
            user = await self.user_client.get_me()
            self.mock_client.get.assert_called_once_with("/users/me")
            self.assertEqual(user.username, "current")
            self.assertEqual(user.id, "current_user")

        asyncio.run(run_test())

    def test_get_user_by_id(self):
        """Test getting user by ID."""
        json_data = {
            "id": "user789",
            "create_at": 1625079600000,
            "update_at": 1625079600000,
            "delete_at": 0,
            "username": "specificuser",
            "nickname": "Specific",
            "first_name": "Specific",
            "last_name": "User",
        }

        self.mock_client.get = AsyncMock(return_value=json_data)

        async def run_test():
            user = await self.user_client.get("user789")
            self.mock_client.get.assert_called_once_with("/users/user789")
            self.assertEqual(user.id, "user789")

        asyncio.run(run_test())


class TestMattermostClient(TestCase):
    def test_client_initialization(self):
        """Test MattermostClient initialization."""
        client = MattermostClient(
            base_url="https://mattermost.example.com", token="test_token"
        )

        self.assertIsNotNone(client.http_client)
        self.assertIsNotNone(client.users)
        self.assertEqual(client.users.obj_class, MMUser)
        self.assertEqual(client.users.name, "user")

    def test_client_headers(self):
        """Test that authorization header is set correctly."""
        token = "bearer_token_xyz"
        client = MattermostClient(
            base_url="https://mattermost.example.com", token=token
        )

        # Check headers were set with correct auth
        headers = client.http_client.headers
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], f"Bearer {token}")

    def test_client_base_url(self):
        """Test that base URL includes API v4 path."""
        client = MattermostClient(
            base_url="https://mattermost.example.com", token="token"
        )

        # The base URL should have /api/v4 appended (convert URL to string for comparison)
        base_url_str = str(client.http_client.base_url)
        self.assertTrue(
            base_url_str.endswith("/api/v4") or base_url_str.endswith("/api/v4/")
        )

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

        asyncio.run(run_test())

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

        asyncio.run(run_test())

    def test_context_manager_full_flow(self):
        """Test full async context manager flow."""

        async def run_test():
            with patch("camille.mattermost.HttpClient") as mock_http_class:
                mock_http_instance = AsyncMock()
                mock_http_class.return_value = mock_http_instance

                client = MattermostClient(
                    base_url="https://mattermost.example.com", token="token"
                )

                async with client as ctx:
                    self.assertEqual(ctx, client)

                mock_http_instance.__aenter__.assert_called_once()
                mock_http_instance.__aexit__.assert_called_once()

        asyncio.run(run_test())

    def test_get_success(self):
        """Test successful GET request."""

        async def run_test():
            client = MattermostClient(
                base_url="https://mattermost.example.com", token="token"
            )

            mock_response = MagicMock()
            mock_response.json.return_value = {"id": "123", "name": "test"}

            client.http_client.get = AsyncMock(return_value=mock_response)

            result = await client.get("/test")

            self.assertEqual(result, {"id": "123", "name": "test"})
            client.http_client.get.assert_called_once_with("/test")
            mock_response.raise_for_status.assert_called_once()

        asyncio.run(run_test())

    def test_get_with_kwargs(self):
        """Test GET request with additional kwargs."""

        async def run_test():
            client = MattermostClient(
                base_url="https://mattermost.example.com", token="token"
            )

            mock_response = MagicMock()
            mock_response.json.return_value = {"result": "ok"}

            client.http_client.get = AsyncMock(return_value=mock_response)

            result = await client.get("/test", params={"key": "value"})

            self.assertEqual(result, {"result": "ok"})
            client.http_client.get.assert_called_once_with(
                "/test", params={"key": "value"}
            )

        asyncio.run(run_test())

    def test_get_http_error(self):
        """Test GET request with HTTP error."""

        async def run_test():
            client = MattermostClient(
                base_url="https://mattermost.example.com", token="token"
            )

            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("404 Not Found")

            client.http_client.get = AsyncMock(return_value=mock_response)

            with pytest.raises(Exception, match="404 Not Found"):
                await client.get("/nonexistent")

        asyncio.run(run_test())

    def test_get_json_parse_error(self):
        """Test GET request with JSON parse error."""

        async def run_test():
            client = MattermostClient(
                base_url="https://mattermost.example.com", token="token"
            )

            mock_response = MagicMock()
            mock_response.json.side_effect = ValueError("Invalid JSON")

            client.http_client.get = AsyncMock(return_value=mock_response)

            with pytest.raises(ValueError, match="Invalid JSON"):
                await client.get("/test")

        asyncio.run(run_test())
