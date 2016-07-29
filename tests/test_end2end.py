# coding: utf-8
"""This test suite checks end-to-end operation of EVE."""

import logging
import os
import shutil
import sys
import tempfile
import time
import unittest

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import deploy.deploy_eve_master
from deploy.cmd import cmd

logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)

SUCCESS = 0
FAILURE = 2
HTTP_PORT = 8999
PB_PORT = 9999
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Test(unittest.TestCase):
    """Base class for test classes

    - Sets-up bitbucket git repo
    - Checks build status
    """
    git_repo = 'git@bitbucket.org:scality/test-eve.git'
    api = None
    eve = None

    def setup_git(self, eve_dir):
        """push the yaml file and the docker context to bitbucket."""
        old_dir = os.getcwd()
        this_dir = os.path.dirname(os.path.abspath(__file__))

        os.chdir(tempfile.mkdtemp())
        cmd('git clone %s' % self.git_repo)
        os.chdir('test-eve')

        try:
            shutil.rmtree('eve')
        except OSError:
            pass

        src_ctxt = os.path.join(this_dir, 'contexts')
        shutil.copytree(src_ctxt, 'eve')

        eve_yaml_file = os.path.join(this_dir, 'yaml', eve_dir, 'main.yml')
        shutil.copy(eve_yaml_file, 'eve')

        cmd('git config user.email "john.doe@example.com"')
        cmd('git config user.name "John Doe"')
        cmd('git config push.default simple')
        cmd('git add -A')
        cmd('git commit --allow-empty -m "changed build ctxt to %s"' % eve_dir)
        cmd('git push')
        os.chdir(old_dir)

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
        self.setup_eve_master()
        self.setup_git('empty_yaml')
        self.assertEqual('failure', self.get_build_status(build_id=1))

    def setup_eve_master(self):
        """Spawns a EVE docker master.

        It will wait until it is up and running.
        """
        sys.argv = [
            'python_unittest',
            'scality/test-eve',
            '-vv',  # very verbose while under heavy development
            '--http_port=%d' % HTTP_PORT,
            '--pb_port=%d' % PB_PORT,
        ]
        self.eve = deploy.deploy_eve_master.main()
        self.api = self.eve.api

    def get_buildbot_log(self):
        """return the contents of master/twistd.log for debugging"""
        return self.eve.docker.execute(self.eve.name, 'cat master/twistd.log')


    def test_git_poll_failure(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a YAML that will fail and check that it fails.
        """
        self.setup_eve_master()
        self.setup_git('expected_fail')
        self.assertEqual('failure', self.get_build_status(build_id=1))

    def test_git_poll_success(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a good YAML with 3 steps (with parallelization) and
        checks that it succeeds.
        """
        self.setup_eve_master()
        self.setup_git('four_stages_sleep')
        self.assertEqual('success', self.get_build_status(build_id=2))

    @unittest.skip("not working right now")
    def test_force_build(self):
        """Tests to force a build.

        Sets up a git, Forces a build and check that it succeeds.
        """
        self.setup_git('four_stages_sleep')
        self.setup_eve_master()
        bootstrap_builder_id = self.api.get_element_id_from_name(
            'builders',
            'bootstrap',
            'builderid')
        self.api.force_build(bootstrap_builder_id, self.git_repo)
        self.assertEqual('success', self.get_build_status(build_id=1))
