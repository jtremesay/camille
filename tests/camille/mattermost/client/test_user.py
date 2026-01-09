from asyncio import run
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from camille.mattermost.client.user import MMUserClient


class TestMMUserClient(IsolatedAsyncioTestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = AsyncMock()
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

        async def run_test():
            user = await self.user_client.get_me()
            self.mock_client.get.assert_called_once_with("/users/me")
            self.assertEqual(user.username, "current")
            self.assertEqual(user.id, "current_user")

        run(run_test())

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

        run(run_test())
