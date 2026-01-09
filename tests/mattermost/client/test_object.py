from datetime import datetime
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from mattermost.testing import MMTestObjectClient


class TestMMObjectClient(IsolatedAsyncioTestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = AsyncMock()
        self.object_client = MMTestObjectClient(self.mock_client)

    async def test_get_object_by_id(self):
        """Test getting object by ID."""
        birthdate = datetime(2023, 1, 1, 0, 0, 0)

        json_data = {
            "id": 1,
            "name": "Test Object",
            "is_active": True,
            "gender": 1.0,
            "birthdate": birthdate.isoformat(),
        }

        self.mock_client.get = AsyncMock(return_value=json_data)

        obj = await self.object_client.get("1")
        self.mock_client.get.assert_awaited_once_with("/testobjects/1")
        self.assertIsNotNone(obj)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.name, "Test Object")
        self.assertTrue(obj.is_active)
        self.assertEqual(obj.gender, 1.0)
        self.assertEqual(obj.birthdate, birthdate)
