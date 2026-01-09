from unittest import TestCase

from mattermost.testing import MMTestObject


class TestMMObject(TestCase):
    """Test base MMObject class."""

    def test_from_json_base_class(self):
        """Test MMObject.from_json base implementation."""
        json_data = {
            "id": 1,
            "name": "Test Object",
            "is_active": True,
            "gender": 1.0,
            "birthdate": "2023-01-01T00:00:00",
        }

        # This would normally fail without actual pydantic fields,
        # but we can test that it calls cls(**data)
        obj = MMTestObject.from_json(json_data)
        self.assertIsInstance(obj, MMTestObject)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.name, "Test Object")
        self.assertTrue(obj.is_active)
        self.assertEqual(obj.gender, 1.0)
