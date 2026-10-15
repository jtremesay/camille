import os
import sys
from unittest import mock

from django.test import SimpleTestCase

from camille.__main__ import main


class MainTests(SimpleTestCase):
    def test_runs_the_django_command_line(self):
        argv = ["camille", "check"]

        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch("django.core.management.execute_from_command_line") as execute,
        ):
            main()

        execute.assert_called_once_with(argv)

    def test_sets_the_default_settings_module(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DJANGO_SETTINGS_MODULE", None)

            with mock.patch("django.core.management.execute_from_command_line"):
                main()

            self.assertEqual(os.environ["DJANGO_SETTINGS_MODULE"], "camille.settings")

    def test_explains_a_missing_django_installation(self):
        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "django.core.management":
                raise ImportError("no django here")

            return real_import(name, *args, **kwargs)

        with (
            mock.patch("builtins.__import__", side_effect=fake_import),
            self.assertRaisesMessage(ImportError, "Couldn't import Django"),
        ):
            main()
