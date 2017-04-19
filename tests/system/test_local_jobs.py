# coding: utf-8
"""This test suite checks end-to-end operation of EVE."""

import os
import unittest

from tests.util.cluster import Cluster


def use_environ(**environ):
    """Decorator to specify extra Eve environment variables."""

    def decorate(func):
        """Set extra Eve environment variables to the given function."""
        func.__eve_environ__ = environ
        func.__old_eve_environ__ = {}
        return func

    return decorate


def frontend_local_job(jobnames):
    """Decorator to add local job(s) to eve config."""

    def decorate(func):
        """Set extra Eve job to the setup of this test."""
        func.__frontend_jobs__ = jobnames
        return func

    return decorate


def backend_local_job(jobnames):
    """Decorator to add local job(s) to eve config."""

    def decorate(func):
        """Set extra Eve job to the setup of this test."""
        func.__backend_jobs__ = jobnames
        return func

    return decorate


PERIODIC_LOCAL_JOB = {
    'scheduler': {
        'type': 'Periodic',
        'name': 'my-periodic-scheduler',
        'periodicBuildTimer': 2,
    },
    'builder': {
        'name': 'my-periodic-builder',
        'description': 'I run periodically',
    },
    'steps': [{
        'ShellCommand': {
            'name': 'type something on console',
            'command': "echo 'hello world'"
        }
    }]
}


class Test(unittest.TestCase):
    def test_local_job_frontend(self, master_ids=(0, )):
        """Test a local job on the frontend.

        The local directory is customized with a subdirectory.

        Steps:
        * Configure local job in decorator
        * Check Eve can start (no error in setup)
        * Verify directories and files (test setup validation)
        * Check schedulers and builders are correct
        """

        cluster = Cluster()
        for master_id in master_ids:
            master = cluster._masters.values()[master_id]
            master.add_conf_file(
                yaml_data=PERIODIC_LOCAL_JOB,
                filename='local2/sub/periodic.yml')
            master.conf['LOCAL_JOBS_DIRPATH'] = 'local2/sub'
            path = os.path.join(master._base_path, 'local2/sub/periodic.yml')
            assert os.path.isfile(path)

        print 'API URL:', cluster.api.api_uri
        cluster.start()
        cluster.sanity_check()
        scheduler = cluster.api.getw(
            '/schedulers',
            get_params={'name': PERIODIC_LOCAL_JOB['scheduler']['name']})
        assert scheduler['enabled']
        builder = cluster.api.getw(
            '/builders',
            get_params={'name': PERIODIC_LOCAL_JOB['builder']['name']})
        assert builder['description'] == PERIODIC_LOCAL_JOB['builder'][
            'description']

        # let job trigger at least once
        buildset = cluster.api.getw(
            '/buildsets',
            get_params={
                'limit': 1,
                'results': 0,  # SUCCESS
            })
        assert buildset['reason'] == "The Periodic scheduler named " \
                                     "'my-periodic-scheduler' " \
                                     "triggered this build"
        cluster.stop()

    def test_local_job_backend(self):
        """Test a local job on the backend.

        The local directory is kept at default value.

        Steps:
        * Configure local job in decorator
        * Check Eve can start (no error in setup)
        * Verify directories and files (test setup validation)
        * Check schedulers and builders are correct
        * Check periodic job is running
        """

        return self.test_local_job_frontend(master_ids=(1, ))

    @unittest.skip('Test not refactored yet')
    @frontend_local_job(["periodic", "nightly"])
    @backend_local_job("nightly")
    def test_local_job_mixed(self):
        """Test a local job on the frontend and backend simultaneously.

        Steps:
        * Configure local jobs in decorators
        * Check Eve can start (no error in setup)
        * Verify directories and files (test setup validation)
        * Check schedulers and builders are correct
        """
        # try:
        #     path = os.path.join(self.test_dir, 'master0/local')
        #     assert os.path.isdir(path)
        #     path = os.path.join(self.test_dir, 'master0/local/periodic.yml')
        #     assert os.path.isfile(path)
        #     path = os.path.join(self.test_dir, 'master0/local/nightly.yml')
        #     assert os.path.isfile(path)
        #     path = os.path.join(self.test_dir, 'master1/local')
        #     assert os.path.isdir(path)
        #     path = os.path.join(self.test_dir, 'master1/local/nightly.yml')
        #     assert os.path.isfile(path)
        #
        #     self.get_builder('my-periodic-builder')
        #     scheduler = self.get_scheduler('my-periodic-scheduler')
        #     assert 'master0' in scheduler['master']['name']
        #     scheduler = self.get_scheduler('nightly-scheduler-test-eve0')
        #     assert 'master0' in scheduler['master']['name']
        #     scheduler = self.get_scheduler('nightly-scheduler-test-eve1')
        #     assert 'master1' in scheduler['master']['name']
        # finally:
        #     # stop eve manually to prevent periodic job from running
        #     self.shutdown_eve()

    @use_environ()
    def test_local_job_empty(self):  # pylint: disable=no-self-use
        """Test local jobs with no job defined and absolute path.

        (useful for people who want to store job files in /etc)

        Steps:
        * Configure local jobs in decorator
        * Check Eve can start (no error in setup)
        * Verify directory (test setup validation)
        """
        cluster = Cluster()
        master = cluster._masters.values()[0]
        master.conf['LOCAL_JOBS_DIRPATH'] = '/dev/null'
        cluster.start()
        cluster.sanity_check()
        cluster.stop()
