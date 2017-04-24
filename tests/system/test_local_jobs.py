"""This test suite checks end-to-end operation of EVE."""

import os
import unittest

from tests.util.cluster import Cluster

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

NIGHTLY_LOCAL_JOB = {
    'scheduler': {
        'type': 'Nightly',
        'name': 'my-nightly-scheduler',
        'hour': 1,
        'minute': 10,
    },
    'builder': {
        'name': 'my-nightly-builder',
        'description': 'I sleep',
    },
    'steps': [{
        'ShellCommand': {
            'name': 'sleep for 1 second',
            'command': "sleep 1"
        }
    }]
}


class TestLocalJobs(unittest.TestCase):
    def configure_local_jobs(self, master_ids=(0, )):
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

    def test_local_job_frontend(self):
        """Test a local job on the frontend.

        The local directory is customized with a subdirectory.

        Steps:
        * Configure local job in decorator
        * Check Eve can start (no error in setup)
        * Verify directories and files (test setup validation)
        * Check schedulers and builders are correct
        """
        self.configure_local_jobs(master_ids=(0, ))

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
        self.configure_local_jobs(master_ids=(1, ))

    def test_local_job_mixed(self):
        """Test a local job on the frontend and backend simultaneously.

        Steps:
        * Configure local jobs in decorators
        * Check Eve can start (no error in setup)
        * Verify directories and files (test setup validation)
        * Check schedulers and builders are correct
        """
        self.configure_local_jobs(master_ids=(0, 1))

    def test_nightly_build(self):
        """Tests that a nightly build is well registred. does not launch it.
        """

        cluster = Cluster()
        master = cluster._masters.values()[0]
        master.add_conf_file(
            yaml_data=NIGHTLY_LOCAL_JOB, filename='local2/sub/nightly.yml')
        master.conf['LOCAL_JOBS_DIRPATH'] = 'local2/sub'
        path = os.path.join(master._base_path, 'local2/sub/nightly.yml')
        assert os.path.isfile(path)

        cluster.start()
        cluster.sanity_check()
        scheduler = cluster.api.getw(
            '/schedulers',
            get_params={'name': NIGHTLY_LOCAL_JOB['scheduler']['name']})
        assert scheduler['enabled']
        builder = cluster.api.getw(
            '/builders',
            get_params={'name': NIGHTLY_LOCAL_JOB['builder']['name']})
        assert builder['description'] == NIGHTLY_LOCAL_JOB['builder'][
            'description']
        cluster.stop()
