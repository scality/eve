# coding: utf-8
"""This test suite checks end-to-end operation of EVE."""

import logging
import os
import platform
import shutil
import socket
import tempfile
import unittest

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from tests.cmd import cmd

logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.getLogger('requests').setLevel(logging.WARNING)

SUCCESS = 0
FAILURE = 2
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def get_master_fqdn():
    """Get the master fqdn.

    Returns:
        str: the fqdn (or ip) of the master the slave can connect to.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("8.8.8.8", 53))
    fqdn = sock.getsockname()[0]
    sock.close()
    return fqdn


class Test(unittest.TestCase):
    """Base class for test classes

    - Sets-up bitbucket git repo
    - Checks build status
    """

    api = None
    eve = None

    def setUp(self):
        self.git_dir = tempfile.mkdtemp(prefix='eve_test_')
        self.top_dir = os.path.dirname((os.path.dirname(
            os.path.abspath(__file__))))
        os.environ['GIT_REPO'] = self.git_dir
        self.setup_eve_master()
        self.setup_git()

    def setup_eve_master(self):
        """Spawns a EVE master.

        It will wait until it is up and running.
        """
        os.chdir(self.top_dir)
        cmd('buildbot stop eve', ignore_exception=True)
        cmd('git clean -fd eve', ignore_exception=True)  # fixme: dangerous!
        cmd('buildbot create-master --relocatable eve')
        os.environ['GIT_KEY_PATH'] = os.path.expanduser('~/.ssh/id_rsa')
        os.environ['MASTER_FQDN'] = get_master_fqdn()
        os.environ['DOCKER_PREFIX'] = 'test-eve'
        cmd('buildbot start eve')

    def setup_git(self):
        """Create a new git repo."""
        os.chdir(self.git_dir)
        cmd('git init .')
        cmd('git config user.email "john.doe@example.com"')
        cmd('git config user.name "John Doe"')
        cmd('echo hello > readme.txt')
        cmd('git add -A')
        cmd('git commit -m "first commit"')

    def commit_git(self, eve_dir):
        """Create a new commit to trigger a test build.

        Args:
            eve_dir (str): directory of the yaml test file.
        """
        os.chdir(self.git_dir)
        src_ctxt = os.path.join(self.top_dir, 'tests', 'contexts')
        shutil.copytree(src_ctxt, 'eve')
        eve_yaml_file = os.path.join(self.top_dir, 'tests',
                                     'yaml', eve_dir, 'main.yml')
        shutil.copy(eve_yaml_file, 'eve')
        cmd('git add -A')

    def build(self, expected_result='success', wait=True):
        """
        Triggers a build, waits for the result and performs sanity checks
        :param expected_result: success or failure
        :return: None
        """
        client = os.path.join(self.top_dir, 'eve', 'client.py')
        out = cmd('python %s --host=localhost --port=%s --passwd=%s %s'
                  % (client, os.environ['TRY_PORT'], os.environ['TRY_PWD'],
                     '--wait' if wait else ''),
                  ignore_exception=(expected_result != 'success'))
        if not wait:
            return
        if expected_result == 'failure':
            assert 'bootstrap: failure (finished)' in out
        elif expected_result == 'cancelled':
            assert 'bootstrap: cancelled (finished)' in out
        else:
            assert 'bootstrap: success (finished)' in out

        log = open(os.path.join(self.top_dir, 'eve', 'twistd.log'), 'r').read()
        if 'Traceback (most recent call last):' in log:
            raise Exception('Found an Exception Traceback in twistd.log')
        if '_mysql_exceptions' in log:
            raise Exception('Found a MySQL issue in twistd.log')

    def test_git_poll_empty_yaml(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a YAML that will fail and check that it fails.
        """
        self.commit_git('empty_yaml')
        self.build(expected_result='failure')

    def test_git_poll_failure(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a YAML that will fail and check that it fails.
        """
        self.commit_git('expected_fail')
        self.build(expected_result='failure')

    def test_git_poll_success(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a good YAML with 3 steps (with parallelization) and
        checks that it succeeds.
        """
        self.commit_git('four_stages_sleep')
        self.build()

    def test_worker_pulls_git_repo(self):
        """Tests git repo caching capabilities
        """
        self.commit_git('worker_pulls_git_repo')
        self.build()

    def test_bad_dockerfile(self):
        """Tests that when a docker file cannot be built, the whole build is
         interrupted.
        """
        self.commit_git('bad_dockerfile')
        self.build(expected_result='failure')

    @unittest.skipIf('RAX_LOGIN' not in os.environ, "needs rackspace credentials")
    def test_openstack_worker(self):
        """Tests git repo caching capabilities
        """
        self.commit_git('openstack_worker')
        self.build()

    def test_write_read_from_cache(self):
        """Tests docker cache volumes

        Step1 creates a docker named volume and creates a file into it.
        Step2 starts another container and reads a file from the same volume.
        """
        self.commit_git('write_read_from_cache')
        self.build()

    @unittest.skipIf('RAX_LOGIN' not in os.environ, "needs rackspace credentials")
    def test_worker_uploads_artifacts(self):
        """Tests artifact uploading to cloudfiles
        """
        self.commit_git('worker_uploads_artifacts')
        self.build()

    def test_skip_if_no_branch_in_yml(self):
        """Tests that the build is cancelled when the branch is not covered
         by the eve/main.yml file
        """
        self.commit_git('branch_not_listed_in_yaml')
        self.build(expected_result='cancelled')

    @unittest.skipIf(platform.system() == 'Darwin', 'Does not work on Mac')
    def test_gollum(self):
        """Tests gollum

        Steps : TODO .
        """
        self.commit_git('gollum')
        self.build()

    def test_ring(self):
        """test a ring like yaml with lots of steps
        Steps :
         * Launch 20 jobs without waiting
         * Launch a last job and wait for the result
        """
        self.commit_git('ring')
        for _ in range(20):
            self.build(wait=False)
        self.build()
