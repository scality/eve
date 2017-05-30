import unittest

from eve.steps.shell_command_with_secrets import ShellCommandWithSecrets


class StepsShellCommandWithSecretsTest(unittest.TestCase):
    def test_constructor(self):
        """Test the __init__ method of the ShellCommandWithSecrets class."""
        self.assertIsNotNone(ShellCommandWithSecrets())
