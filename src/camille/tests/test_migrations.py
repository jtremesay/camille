from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class CreateProfilesMigrationTests(TransactionTestCase):
    before = [("camille", "0001_profile")]
    after = [("camille", "0002_create_profiles")]

    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_backfills_profiles_for_existing_users(self):
        apps = self.migrate(self.before)
        User = apps.get_model("auth", "User")
        Profile = apps.get_model("camille", "Profile")
        orphan = User.objects.create(username="orphan")
        covered = User.objects.create(username="covered")
        existing = Profile.objects.create(user=covered)

        apps = self.migrate(self.after)
        Profile = apps.get_model("camille", "Profile")

        self.assertEqual(Profile.objects.count(), 2)
        self.assertTrue(Profile.objects.filter(user_id=orphan.pk).exists())
        self.assertEqual(Profile.objects.get(user_id=covered.pk).pk, existing.pk)
