"""This test suite checks end-to-end operation of EVE."""
import os
import unittest


@unittest.skip('Not refactored yet')
class Test(unittest.TestCase):
    @unittest.skipIf('RAX_LOGIN' not in os.environ,
                     'needs rackspace credentials')
    def test_openstack_worker(self):
        """Tests git repo caching capabilities
        """
        # self.commit_git('openstack_worker')
        # self.notify_webhook()
        # self.get_build_result(expected_result='success')

    @unittest.skipIf('RAX_LOGIN' not in os.environ,
                     'needs rackspace credentials')
    def test_bad_substantiate(self):
        """Ensures that a bad latent worker substantiation fails the build.

        Steps:
         * Try to substantiate a bad latent worker
         * Verify the build is in failed state afterward
        """
        # self.commit_git('bad_substantiate')
        # self.notify_webhook()
        # self.get_build_result(expected_result='failure')

    @unittest.skip('Really slow (5 minutes)')
    def test_use_broken_openstack(self):
        """Test the retry mechanism when OpenStack spawning fails.

        Steps:
         * Substantiate an openstack worker with an inexisting image and no
         credentials
         * Expect a failure after 5 minutes or so
        """
        # self.commit_git('use_broken_openstack')
        # self.notify_webhook()
        # self.get_build_result(expected_result='failure')
