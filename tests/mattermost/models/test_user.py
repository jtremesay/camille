from unittest import TestCase

from mattermost.models import MMUser


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
