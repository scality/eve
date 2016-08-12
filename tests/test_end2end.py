# coding: utf-8
"""This test suite checks end-to-end operation of EVE."""

import logging
import os
import shutil
import sys
import tempfile
import time
import unittest

import docker
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from tests.buildbot_api_client import BuildbotDataAPI
from tests.cmd import cmd

logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)

SUCCESS = 0
FAILURE = 2
HTTP_PORT = os.environ['HTTP_PORT']
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Test(unittest.TestCase):
    """Base class for test classes

    - Sets-up bitbucket git repo
    - Checks build status
    """

    docker = docker.AutoVersionClient()

    def setUp(self):
        self.setup_git()
        self.setup_eve_master()
        self.api = BuildbotDataAPI('http://localhost:%s' % HTTP_PORT)

    def setup_git(self):
        """push the yaml file and the docker context to bitbucket."""
        self.docker.build(path='tests/git-daemon-docker', tag='git-daemon')
        self.docker.remove_container('git-daemon', force=True)
        container = self.docker.create_container(
            name='git-daemon',
            image='git-daemon',
            host_config=self.docker.create_host_config(
                port_bindings={9418: ('127.0.0.1', 9418)},
            ),
        )
        self.docker.start(container=container.get('Id'))

        self.git_dir = tempfile.mkdtemp(prefix='eve_test_')
        cwd = os.getcwd()
        os.environ['GIT_REPO'] = 'git://git-daemon:9418/repo.git'
        os.chdir(self.git_dir)
        cmd('git clone git://127.0.0.1:9418/repo.git .')
        cmd('git config user.email "john.doe@example.com"')
        cmd('git config user.name "John Doe"')
        cmd('git config push.default simple')
        os.chdir(cwd)

    def setup_eve_master(self):
        """Spawns a EVE docker master.

        It will wait until it is up and running.
        """
        cmd('buildbot create-master --relocatable eve')
        cmd('buildbot start eve')

    def commit_git(self, eve_dir):
        cwd = os.getcwd()
        os.chdir(self.git_dir)
        this_dir = os.path.dirname(os.path.abspath(__file__))

        src_ctxt = os.path.join(this_dir, 'contexts')
        shutil.copytree(src_ctxt, 'eve')

        eve_yaml_file = os.path.join(this_dir, 'yaml', eve_dir, 'main.yml')
        shutil.copy(eve_yaml_file, 'eve')

        cmd('git add -A')
        cmd('git commit --allow-empty -m "changed build ctxt to %s"' % eve_dir)
        cmd('git push')

        os.chdir(cwd)

    def get_buildbot_log(self):
        """return the contents of master/twistd.log for debugging"""
        return cmd('cat eve/twistd.log')

    def get_build_status(self, build_id, timeout=120):
        """Wait for the build to finish and get build status from buildbot.

        See `Build Result Codes`_ for more details on build status.

        .. _Build Result Codes:
          http://docs.buildbot.net/latest/developer/results.html
        """
        state = None
        for _ in range(timeout):
            time.sleep(1)
            log = self.get_buildbot_log()
            if 'Traceback (most recent call last):' in log:
                logger.error(log)
                raise Exception('Found an Exception Traceback in twistd.log')
            try:
                build = self.api.get('builds/%d' % build_id)['builds'][0]
            except requests.HTTPError as exp:
                logger.info('Build did not start yet. API responded: %s',
                            exp.message)
                continue
            state = build['state_string']
            logger.info('API responded: BUILD STATE = %s', state)
            if state not in ('starting', 'created'):
                if build['results'] is not None:
                    break
                logger.info('API says that the job is finished but '
                            'there are no results => retrying!')

        self.assertEqual('finished', state)
        # Bitbucket API bug. Happens sometimes!
        self.assertIsNotNone(build['results'], 'finished but no results=> bug')
        result_codes = ['success', 'warnings', 'failure', 'skipped',
                        'exception', 'cancelled']
        return result_codes[int(build['results'])]

    def test_git_poll_empty_yaml(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a YAML that will fail and check that it fails.
        """
        self.commit_git('empty_yaml')
        self.assertEqual('failure', self.get_build_status(build_id=1))

    def test_git_poll_failure(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a YAML that will fail and check that it fails.
        """
        self.commit_git('expected_fail')
        self.assertEqual('failure', self.get_build_status(build_id=1))

    def test_git_poll_success(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a good YAML with 3 steps (with parallelization) and
        checks that it succeeds.
        """
        self.commit_git('four_stages_sleep')
        self.assertEqual('success', self.get_build_status(build_id=2))

