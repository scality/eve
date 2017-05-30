import shutil
import time
import unittest
from math import ceil
from tempfile import mkdtemp

import eve.setup.misc
from buildbot.plugins import util


class SetupMiscTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = mkdtemp()
        open('%s/ca.pem' % self.tmpdir, 'w').close()
        open('%s/key.pem' % self.tmpdir, 'w').close()
        open('%s/cert.pem' % self.tmpdir, 'w').close()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_verify_docker_certificates(self):
        """Test the verify_docker_certificate function."""
        util.env = util.load_env([
            ('DOCKER_TLS_VERIFY', True),
            ('DOCKER_CERT_PATH', self.tmpdir)
        ])
        eve.setup.misc.verify_docker_certificates()

    def test_verify_docker_certificates_no_cert_path(self):
        """Test the very_docker_certificate function
        with no TLS verification.
        """
        util.env = util.load_env([
            ('DOCKER_TLS_VERIFY', False)
        ])
        eve.setup.misc.verify_docker_certificates()

    def test_properties(self):
        """Test the properties function."""
        self.assertIsNotNone(eve.setup.misc.properties())

    def test_wamp(self):
        """Test the wamp function."""
        util.env = util.load_env([
            ('WAMP_REALM', 'bar'),
            ('WAMP_ROUTER_URL', 'foo')
        ])
        self.assertIsNotNone(eve.setup.misc.wamp())

    def test_protocols(self):
        """Test the protocols function."""
        util.env = util.load_env([
            ('PB_PORT', '12345'),
        ])
        self.assertIsNotNone(eve.setup.misc.protocols())

    def test_register_starttime(self):
        """Test the register_starttime function."""
        eve.setup.misc.register_starttime()
        self.assertGreaterEqual(ceil(time.time()),
                                ceil(float(util.env.MASTER_START_TIME)))
