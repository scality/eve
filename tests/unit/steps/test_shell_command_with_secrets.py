"""Unit tests of `eve.steps.shell_command_with_secrets`."""

import unittest

from eve.steps.shell_command_with_secrets import ShellCommandWithSecrets


class StepsShellCommandWithSecretsTest(unittest.TestCase):
    def test_constructor(self):
        self.assertIsNotNone(ShellCommandWithSecrets())
