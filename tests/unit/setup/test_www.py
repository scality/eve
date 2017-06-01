"""Unit tests of `eve.setup.www`."""

import unittest

from buildbot.plugins import util

import eve.setup.www


class TestDenyRebuildIntermediateBuild(unittest.TestCase):
    def test_init(self):
        ctx = eve.setup.www.DenyRebuildIntermediateBuild('foo', role='*')
        self.assertEquals(ctx.root_builder_name, 'foo')


class TestSetupWww(unittest.TestCase):
    def test_www(self):
        util.env = util.load_env([
            ('HTTP_PORT', '8080')
        ])
        self.assertIsNotNone(eve.setup.www.www())

    def test_auth_oauth2(self):
        util.env = util.load_env([
            ('OAUTH2_CLIENT_ID', 'foo'),
            ('OAUTH2_PROVIDER', 'bitbucket'),
            ('OAUTH2_CLIENT_SECRET', 'foo'),
        ])
        self.assertIsNotNone(eve.setup.www.auth())

    def test_auth_www(self):
        util.env = util.load_env([
            ('OAUTH2_CLIENT_ID', ''),
            ('WWW_PLAIN_LOGIN', 'foo'),
            ('WWW_PLAIN_PASSWORD', 'foo'),
        ])
        self.assertIsNotNone(eve.setup.www.auth())

    def test_auth_no_auth(self):
        util.env = util.load_env([
            ('OAUTH2_CLIENT_ID', ''),
            ('WWW_PLAIN_LOGIN', ''),
            ('WWW_PLAIN_PASSWORD', 'foo'),
        ])
        self.assertIsNotNone(eve.setup.www.auth())

    def test_authz_default(self):
        util.env = util.load_env([
            ('OAUTH2_CLIENT_ID', ''),
            ('WWW_PLAIN_LOGIN', ''),
        ])
        self.assertIsNotNone(eve.setup.www.authz())

    def test_authz_client(self):
        util.env = util.load_env([
            ('BOOTSTRAP_BUILDER_NAME', 'foo'),
            ('OAUTH2_CLIENT_ID', 'foo'),
            ('OAUTH2_GROUP', 'foo'),
        ])
        self.assertIsNotNone(eve.setup.www.authz())

    def test_authz_group(self):
        util.env = util.load_env([
            ('BOOTSTRAP_BUILDER_NAME', 'foo'),
            ('OAUTH2_CLIENT_ID', ''),
            ('OAUTH2_GROUP', 'foo'),
            ('WWW_PLAIN_LOGIN', 'foo'),
        ])
        self.assertIsNotNone(eve.setup.www.authz())
