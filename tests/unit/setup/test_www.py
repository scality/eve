import unittest

import eve.setup.www
from buildbot.plugins import util


class TestDenyRebuildIntermediateBuild(unittest.TestCase):
    def test_constructor(self):
        """Test the __init__ method of the DenyRebuildIntermediatebuild
        class.
        """
        ctx = eve.setup.www.DenyRebuildIntermediateBuild('foo', role='*')
        self.assertEquals(ctx.root_builder_name, 'foo')


class TestSetupWww(unittest.TestCase):
    def test_www(self):
        """
        Test that the www function is run without throwing an exception and
        that it returns anything else than None.
        """
        # yapf: disable
        util.env = util.load_env([
            ('HTTP_PORT', '8080')
        ])
        self.assertTrue(eve.setup.www.www() is not None)

    def test_auth_oauth2(self):
        """Test the auth function with oauth2 support."""
        # yapf: disable
        util.env = util.load_env([
            ('OAUTH2_CLIENT_ID', 'foo'),
            ('OAUTH2_PROVIDER', 'bitbucket'),
            ('OAUTH2_CLIENT_SECRET', 'foo'),
        ])
        self.assertTrue(eve.setup.www.auth() is not None)

    def test_auth_www(self):
        """Test the www function with www support."""
        # yapf: disable
        util.env = util.load_env([
            ('OAUTH2_CLIENT_ID', ''),
            ('WWW_PLAIN_LOGIN', 'foo'),
            ('WWW_PLAIN_PASSWORD', 'foo'),
        ])
        self.assertTrue(eve.setup.www.auth() is not None)

    def test_auth_no_auth(self):
        """Test the auth function is no authentication support."""
        # yapf: disable
        util.env = util.load_env([
            ('OAUTH2_CLIENT_ID', ''),
            ('WWW_PLAIN_LOGIN', ''),
            ('WWW_PLAIN_PASSWORD', 'foo'),
        ])
        self.assertTrue(eve.setup.www.auth() is not None)

    def test_authz_default(self):
        """Test the authz function is no authentication support."""
        # yapf: disable
        util.env = util.load_env([
            ('OAUTH2_CLIENT_ID', ''),
            ('WWW_PLAIN_LOGIN', ''),
        ])
        self.assertTrue(eve.setup.www.authz() is not None)

    def test_authz_client(self):
        """Test the authz function with oauth2 client id."""
        # yapf: disable
        util.env = util.load_env([
            ('BOOTSTRAP_BUILDER_NAME', 'foo'),
            ('OAUTH2_CLIENT_ID', 'foo'),
            ('OAUTH2_GROUP', 'foo'),
        ])
        self.assertTrue(eve.setup.www.authz() is not None)

    def test_authz_group(self):
        """Test the authz function with oauth2 group."""
        # yapf: disable
        util.env = util.load_env([
            ('BOOTSTRAP_BUILDER_NAME', 'foo'),
            ('OAUTH2_CLIENT_ID', ''),
            ('OAUTH2_GROUP', 'foo'),
            ('WWW_PLAIN_LOGIN', 'foo'),
        ])
        self.assertTrue(eve.setup.www.authz() is not None)
