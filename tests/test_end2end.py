# coding: utf-8
"""This test suite checks end-to-end operation of EVE."""

import logging
import os
import shutil
import socket
import tempfile
import time
import unittest

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from tests.buildbot_api_client import BuildbotDataAPI

from tests.cmd import cmd

logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.getLogger('requests').setLevel(logging.WARNING)

SUCCESS = 0
FAILURE = 2
HTTP_PORT = 8999
PB_PORT = 9999
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def setup_eve_master():
    """Spawns a EVE master.

    It will wait until it is up and running.
    """
    cmd('buildbot stop eve', ignore_exception=True)
    cmd('git clean -fd eve', ignore_exception=True)
    cmd('buildbot create-master --relocatable eve')
    os.environ['GIT_KEY_PATH'] = os.path.expanduser('~/.ssh/id_rsa')
    os.environ['MASTER_FQDN'] = get_master_fqdn()
    os.environ['DOCKER_PREFIX'] = 'test-eve'
    cmd('buildbot start eve')


def get_master_fqdn():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("8.8.8.8", 53))
    fqdn = sock.getsockname()[0]
    sock.close()
    return fqdn


def get_buildbot_log():
    """return the contents of master/twistd.log for debugging"""
    return open('eve/twistd.log').read()


class Test(unittest.TestCase):
    """Base class for test classes

    - Sets-up bitbucket git repo
    - Checks build status
    """

    git_repo = 'git@bitbucket.org:scality/test-eve.git'
    api = None
    eve = None

    def setUp(self):
        self.setup_git()
        setup_eve_master()
        self.api = BuildbotDataAPI('http://localhost:%s/api/v2/' % HTTP_PORT)

    def setup_git(self):
        """push the yaml file and the docker context to bitbucket."""
        self.git_dir = tempfile.mkdtemp(prefix='eve_test_')
        cwd = os.getcwd()
        os.environ['GIT_REPO'] = self.git_repo
        os.chdir(self.git_dir)
        cmd('git clone %s .' % self.git_repo)
        cmd('git config user.email "john.doe@example.com"')
        cmd('git config user.name "John Doe"')
        cmd('git config push.default simple')
        os.chdir(cwd)

    def commit_git(self, eve_dir):
        cwd = os.getcwd()
        os.chdir(self.git_dir)
        this_dir = os.path.dirname(os.path.abspath(__file__))

        src_ctxt = os.path.join(this_dir, 'contexts')
        shutil.rmtree('eve')
        shutil.copytree(src_ctxt, 'eve')

        eve_yaml_file = os.path.join(this_dir, 'yaml', eve_dir, 'main.yml')
        shutil.copy(eve_yaml_file, 'eve')

        cmd('git add -A')
        cmd('git commit --allow-empty -m "changed build ctxt to %s"' % eve_dir)
        os.chdir(cwd)
        for _ in range(40):
            time.sleep(1)
            if 'gitpoller: processing changes from' in get_buildbot_log():
                break

            logger.info('Waiting for gitpoller to start')
        else:
            raise Exception('gitpoller did not start')

        os.chdir(self.git_dir)
        cmd('git push')
        os.chdir(cwd)

    def get_build_status(self, build_id, timeout=120):
        """Wait for the build to finish and get build status from buildbot.

        See `Build Result Codes`_ for more details on build status.

        .. _Build Result Codes:
          http://docs.buildbot.net/latest/developer/results.html
        """
        state = None
        for _ in range(timeout):
            time.sleep(1)
            log = get_buildbot_log()
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
            if state not in ('starting', 'created', 'building'):
                if build['results'] is not None:
                    break
                logger.info('API says that the job is finished (%s) but '
                            'there are no results => retrying!', state)

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
        self.assertEqual('success', self.get_build_status(build_id=1))

    def test_worker_pulls_git_repo(self):
        """Tests git repo caching capabilities
        """
        self.commit_git('worker_pulls_git_repo')
        self.assertEqual('success', self.get_build_status(build_id=1))

    def test_write_read_from_cache(self):
        """Tests docker cache volumes

        Step1 creates a docker named volume and creates a file into it.
        Step2 starts another container and reads a file from the same volume.
        """
        self.commit_git('write_read_from_cache')
        self.assertEqual('success', self.get_build_status(build_id=1))

    @unittest.skip("needs rackspace credentials")
    def test_worker_uploads_artifacts(self):
        """Tests artifact uploading to cloudfiles
        """
        self.commit_git('worker_uploads_artifacts')
        self.assertEqual('success', self.get_build_status(build_id=1))

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
