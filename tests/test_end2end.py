# coding: utf-8
"""This test suite checks end-to-end operation of EVE."""

from __future__ import print_function

import json
import logging
import os
import shutil
import socket
import tempfile
import time
import unittest

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from . import buildbot_api_client
from tests.cmd import cmd

logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.getLogger('requests').setLevel(logging.WARNING)

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_TRY_PORT = 7990
BASE_HTTP_PORT = 8990
BASE_PB_PORT = 9990
WAMP_PORT = 10990


def get_master_fqdn():
    """Get the master fqdn.

    Returns:
        str: the fqdn (or ip) of the master the worker can connect to.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("8.8.8.8", 53))
    fqdn = sock.getsockname()[0]
    sock.close()
    return fqdn


class Test(unittest.TestCase):  # pylint: disable=too-many-public-methods
    """Base class for test classes

    - Sets-up bitbucket git repo
    - Checks build status
    """

    webhook_url = 'http://localhost:%d/change_hook/bitbucket'
    api = None
    eve = None

    def setUp(self):
        self.git_dir = tempfile.mkdtemp(prefix='eve_test_')
        self.top_dir = os.path.dirname((os.path.dirname(
            os.path.abspath(__file__))))
        self.test_dir = os.path.join(os.path.expanduser('~/.eve_test_data'))
        try:
            self.shutdown_eve()
        except OSError:
            pass
        os.environ['GIT_REPO'] = 'git@bitbucket.org:scality/mock.git'
        os.environ['LOCAL_GIT_REPO'] = self.git_dir
        self.url = 'http://localhost:%d/' % (BASE_HTTP_PORT)
        os.environ['EXTERNAL_URL'] = self.url
        self.setup_crossbar()
        self.setup_eve_master_frontend(master_id=0)
        self.setup_eve_master_backend(master_id=1)
        self.setup_eve_master_backend(master_id=2)
        self.api = buildbot_api_client.BuildbotDataAPI(self.url + 'api/v2/')
        self.setup_git()

    def shutdown_eve(self):
        """Stop Eve masters and crossbar instances."""
        for filename in os.listdir(self.test_dir):
            filepath = os.path.join(self.test_dir, filename)
            if filename.startswith('master'):
                cmd('buildbot stop %s' % filepath, ignore_exception=True)
            elif filename.startswith('crossbar'):
                cmd('crossbar stop --cbdir %s' %
                    filepath, ignore_exception=True)

        cmd('rm -rf %s' % self.test_dir, ignore_exception=True)

    def setup_eve_master_frontend(self, master_id):
        """Spawns a EVE master frontend.

        It will wait until it is up and running.
        """
        os.environ['TRY_PORT'] = str(BASE_TRY_PORT + master_id)
        os.environ['HTTP_PORT'] = str(BASE_HTTP_PORT + master_id)
        self.setup_eve_master(master_id, master_type='frontend')

    def setup_eve_master_backend(self, master_id):
        """Spawns a EVE master backend.

        It will wait until it is up and running.
        """
        os.environ['GIT_KEY_PATH'] = os.path.expanduser('~/.ssh/id_rsa')
        os.environ['MASTER_FQDN'] = get_master_fqdn()
        os.environ['MASTER_NAME'] = 'master%d' % master_id
        os.environ['WORKER_SUFFIX'] = 'test-eve%d' % master_id

        os.environ['PB_PORT'] = str(BASE_PB_PORT + master_id)
        os.environ['MAX_LOCAL_WORKERS'] = '1'
        self.setup_eve_master(master_id, master_type='backend')

    def setup_eve_master(self, master_id, master_type):
        """Spawns a EVE master backend.

        It will wait until it is up and running.
        """

        sql_path = os.path.join(self.test_dir, 'state.sqlite')
        os.environ['DB_URL'] = 'sqlite:///' + sql_path

        os.environ['WAMP_ROUTER_URL'] = 'ws://localhost:%d/ws' % WAMP_PORT
        os.environ['WAMP_REALM'] = 'buildbot'

        master_cfg_dir = os.path.join(self.top_dir, 'eve', 'master')

        masterdir = os.path.join(self.test_dir, 'master%i' % master_id)
        cmd('mkdir -p %s' % masterdir, ignore_exception=True)
        os.chdir(masterdir)
        cmd('cp -r %s/* .' % master_cfg_dir)
        cmd('mv %s.master.cfg master.cfg' % master_type)

        cmd('buildbot create-master --relocatable --db=%s .' %
            os.environ['DB_URL'])

        cmd('buildbot start .')

    def setup_crossbar(self):
        """Spawns a local crossbar.
        """
        crossbar_dir = os.path.join(self.test_dir, 'crossbar')
        cmd('mkdir -p %s' % crossbar_dir, ignore_exception=True)
        crossbar_cfg_path = os.path.join(
            self.top_dir, 'tests', 'crossbar.json')
        os.chdir(crossbar_dir)

        cmd('cp %s %s' % (crossbar_cfg_path,
                          os.path.join(crossbar_dir, 'config.json')))
        cmd('crossbar start --logtofile --cbdir %s' % crossbar_dir, wait=False)

    def setup_git(self):
        """Create a new git repo."""

        bitbucket_cache_dir = os.path.join(self.top_dir, 'eve', 'master',
                                           'services', 'bitbucket_cache')
        cmd('docker build -t bitbucket.org %s' % bitbucket_cache_dir)
        cmd('docker rm -f bitbucket.org', ignore_exception=True)
        self.git_cache_docker_id = cmd('docker run -d -p 2222:22 '
                                       '--name bitbucket.org bitbucket.org')
        time.sleep(1)
        os.chdir(self.git_dir)
        cmd('git clone '
            'git+ssh://git@localhost:2222/home/git/scality/mock.git .')
        cmd('git config user.email "john.doe@example.com"')
        cmd('git config user.name "John Doe"')
        cmd('echo hello > readme.txt')
        cmd('git add -A')
        cmd('git commit -m "first commit"')
        cmd('git push')

    def commit_git(self, eve_dir):
        """Create a new commit to trigger a test build.

        Args:
            eve_dir (str): directory of the yaml test file.
        """
        os.chdir(self.git_dir)
        src_ctxt = os.path.join(self.top_dir, 'tests', 'contexts')
        shutil.rmtree('eve', ignore_errors=True)
        shutil.copytree(src_ctxt, 'eve')
        eve_yaml_file = os.path.join(self.top_dir, 'tests',
                                     'yaml', eve_dir, 'main.yml')
        shutil.copy(eve_yaml_file, 'eve')
        cmd('git add -A')
        cmd('git commit -m "add %s"' % eve_yaml_file)
        cmd('git push')

    def notify_webhook(self):
        """Notify Eve's bitbucket hook of a new change."""
        commits = []
        res = cmd('git log --pretty=format:"%an %ae|%s|%H|%cd" --date=iso')
        for line in reversed(res.splitlines()):
            author, message, revision, _ = line.split('|')
            commits.append({
                'new': {
                    'type': 'branch',
                    'target': {
                        'hash': revision,
                        'author': {'raw': author},
                        'message': message,
                        'links': {
                            'html': {'href': revision}
                        },
                    },
                    'name': 'master'
                }
            })

        payload = {
            'repository': {
                'links': {
                    'html': {
                        'href': 'https://bitbucket.org/scality/test'
                    }
                },
                'scm': 'git',
                'project': {'name': 'TEST'},
            },
            'push': {
                'changes': commits
            },
            'commits': commits,
        }
        requests.post(self.webhook_url % BASE_HTTP_PORT,
                      data=json.dumps(payload))

    def get_bootstrap_builder(self):
        """Get builder named 'bootstrap' from the Buildbot's API."""
        return self.api.get('builders?name=bootstrap')['builders'][0]

    def get_bootstrap_build(self, build_number=1):
        """Wait for build 'bootstrap' to start and return its infos."""
        builder = self.get_bootstrap_builder()
        for _ in range(10):
            try:
                return self.api.get(
                    'builds?builderid=%d&number=%d' %
                    (builder['builderid'], build_number))['builds'][0]
            except IndexError:
                time.sleep(1)
                print('waiting for build to start')
        raise Exception('unable to find bootstrap build, '
                        'builderid=%d, build_number=%d' %
                        (builder['builderid'], build_number))

    def get_build_result(self, build_number=1, expected_result='success'):
        """Get the result of the build `build_number`."""
        for _ in range(900):
            build = self.get_bootstrap_build(build_number=build_number)
            if build['state_string'] == 'finished' and \
                    build['results'] is not None:
                break
            time.sleep(1)
            print('waiting for build to finish')
        else:
            raise Exception('Build took too long')
        result_codes = ['success', 'warnings', 'failure', 'skipped',
                        'exception', 'retry', 'cancelled']
        assert result_codes[build['results']] == expected_result
        return build

    def test_git_poll_empty_yaml(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a YAML that will fail and check that it fails.
        """
        self.commit_git('empty_yaml')
        self.notify_webhook()
        self.get_build_result(expected_result='failure')

    def test_git_poll_failure(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a YAML that will fail and check that it fails.
        """
        self.commit_git('expected_fail')
        self.notify_webhook()
        self.get_build_result(expected_result='failure')

    def test_git_poll_success(self):
        """Tests builds triggered by git polling.

        Spawns EVE, sends a good YAML with 3 steps (with parallelization) and
        checks that it succeeds.
        """
        self.commit_git('four_stages_sleep')
        self.notify_webhook()
        self.get_build_result(expected_result='success')

    def test_two_masters(self):
        """Tests that multi master mode works
        """
        self.commit_git('four_stages_sleep')
        self.notify_webhook()
        time.sleep(10)
        self.commit_git('ring')
        self.notify_webhook()
        self.get_build_result(expected_result='success')
        self.get_build_result(expected_result='success')

    def test_worker_pulls_git_repo(self):
        """Tests git repo caching capabilities
        """
        self.commit_git('worker_pulls_git_repo')
        self.notify_webhook()
        self.get_build_result(expected_result='success')

    def test_bad_dockerfile(self):
        """Tests that when a docker file cannot be built, the whole build is
         interrupted.
        """
        self.commit_git('bad_dockerfile')
        self.notify_webhook()
        self.get_build_result(expected_result='failure')

    @unittest.skipIf('RAX_LOGIN' not in os.environ,
                     'needs rackspace credentials')
    def test_openstack_worker(self):
        """Tests git repo caching capabilities
        """
        self.commit_git('openstack_worker')
        self.notify_webhook()
        self.get_build_result(expected_result='success')

    def test_write_read_from_cache(self):
        """Tests docker cache volumes

        Step1 creates a docker named volume and creates a file into it.
        Step2 starts another container and reads a file from the same volume.
        """
        self.commit_git('write_read_from_cache')
        self.notify_webhook()
        self.get_build_result(expected_result='success')

    @unittest.skipIf('ARTIFACTS_LOGIN' not in os.environ,
                     'needs artifacts credentials')
    @unittest.skipIf('RAX_LOGIN' not in os.environ,
                     'needs rackspace credentials')
    def test_worker_uploads_artifacts(self):
        """Tests artifact uploading to cloudfiles
        """
        self.commit_git('worker_uploads_artifacts')
        self.notify_webhook()
        self.get_build_result(expected_result='success')

    def test_skip_if_no_branch_in_yml(self):
        """Tests that the build is cancelled when the branch is not covered
         by the eve/main.yml file
        """
        self.commit_git('branch_not_listed_in_yaml')
        self.notify_webhook()
        self.get_build_result(expected_result='cancelled')

    @unittest.skip('Needs authenticated git access')
    def test_gollum(self):
        """Tests gollum install / project creation.

        Step1 creates a docker and install gollum on it.
        Step2 create a new gollum project
        Step3 run sample tests in this newly created gollum project
        """
        self.commit_git('gollum')
        self.notify_webhook()
        self.get_build_result(expected_result='success')

    def test_lost_slave_recovery(self):
        """Ensures test can recover when slave is lost.

        Steps :
         * Launch the first job, that kills buildbot/container
         * Launch again, detect it is a retry, and just pass
        """
        self.commit_git('lost_slave_recovery')
        self.notify_webhook()
        self.get_build_result(expected_result='success')

    @unittest.skipIf('RAX_LOGIN' not in os.environ,
                     'needs rackspace credentials')
    def test_bad_substantiate(self):
        """Ensures that a bad latent worker substantiation fails the build.

        Steps:
         * Try to substantiate a bad latent worker
         * Verify the build is in failed state afterward
        """
        self.commit_git('bad_substantiate')
        self.notify_webhook()
        self.get_build_result(expected_result='failure')

    def test_docker_in_docker(self):
        """Tests that we can launch a docker command inside a docker worker

        Steps:
         * Substantiate a docker worker containing docker installation
         * Launch a `docker ps` command
         * Check that it succeeds
        """
        self.commit_git('docker_in_docker')
        self.notify_webhook()
        self.get_build_result(expected_result='success')

    def test_use_premade_docker_image(self):
        """Tests that we can build docker images on our own and give them to
        buildbot

        Steps:
         * Substantiate a docker worker containing docker installation
         * Launch a `docker build` command
         * Launch a stage with the newly built image
         * Check that it succeeds
        """
        self.commit_git('use_premade_docker_image')
        self.notify_webhook()
        self.get_build_result(expected_result='success')

    def test_use_different_dockerfile(self):
        """Test to build Docker image with a different Dockerfile.

        By default, ``docker build`` use the dockerfile named
        **/Dockerfile** inside the Docker context.
        We can use a different Dockerfile (see ``-f`` option of
        ``docker build`` command).
        """
        self.commit_git('use_different_dockerfile')
        self.notify_webhook()
        self.get_build_result(expected_result='success')
