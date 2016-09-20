# coding: utf-8
"""This test suite checks end-to-end operation of EVE."""

import logging
import os
import platform
import shutil
import socket
import tempfile
import time
import unittest


import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from tests.cmd import cmd
import buildbot_api_client

logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.getLogger('requests').setLevel(logging.WARNING)

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_TRY_PORT = 7990
BASE_HTTP_PORT = 8990
BASE_PB_PORT = 9990

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
        self.test_dir = os.path.join(self.top_dir, '.test')
        try:
            self.shutdown_eve()
        except OSError:
            pass
        os.environ['GIT_REPO'] = self.git_dir
        self.url = 'http://localhost:%d/' % (BASE_HTTP_PORT + 1)
        os.environ['EXTERNAL_URL'] = self.url
        self.setup_eve_master(master_id=1)
        self.setup_eve_master(master_id=2)
        self.api = buildbot_api_client.BuildbotDataAPI(self.url + 'api/v2/')
        self.setup_git()

    def shutdown_eve(self):
        for filename in os.listdir(self.test_dir):
            if not filename.startswith('master'):
                continue
            filpath = os.path.join(self.test_dir, filename)
            cmd('buildbot stop %s' % filpath, ignore_exception=True)
        cmd('rm -rf %s' % self.test_dir)


    def setup_eve_master(self, master_id=1):
        """Spawns a EVE master.

        It will wait until it is up and running.
        """
        masterdir = os.path.join(self.top_dir, '.test', 'master%i' % master_id)
        cmd('mkdir -p %s' % masterdir, ignore_exception=True)
        master_cfg_path = os.path.join(self.top_dir, 'eve', 'master.cfg')
        os.chdir(masterdir)

        cmd('cp %s .' % master_cfg_path)

        sql_path = os.path.join(self.top_dir, '.test', 'state.sqlite')
        os.environ['DB_URL'] = 'sqlite:///' + sql_path

        cmd('buildbot create-master --relocatable --db=%s .' % os.environ['DB_URL'])
        os.environ['GIT_KEY_PATH'] = os.path.expanduser('~/.ssh/id_rsa')
        os.environ['MASTER_FQDN'] = get_master_fqdn()
        os.environ['MASTER_NAME'] = 'master%d' % master_id
        os.environ['WORKER_SUFFIX'] = 'test-eve%d' % master_id
        os.environ['TRY_PORT'] = str(BASE_TRY_PORT + master_id)
        os.environ['HTTP_PORT'] = str(BASE_HTTP_PORT + master_id)
        os.environ['PB_PORT'] = str(BASE_PB_PORT + master_id)
        os.environ['MAX_LOCAL_WORKERS'] = '1'

        cmd('buildbot start .')

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
        shutil.rmtree('eve', ignore_errors=True)
        shutil.copytree(src_ctxt, 'eve')
        eve_yaml_file = os.path.join(self.top_dir, 'tests',
                                     'yaml', eve_dir, 'main.yml')
        shutil.copy(eve_yaml_file, 'eve')
        cmd('git add -A')
        cmd('git commit -m "add %s"' % eve_yaml_file)

    def notify_webhook(self, master_id=1):
        commits = []
        res = cmd('git log --pretty=format:"%an %ae|%s|%H|%cd" --date=iso')
        for line in reversed(res.splitlines()):
            author, message, revision, timestamp = line.split('|')
            commits.append({
                'raw_author': author,
                'files': [{'file': 'eve/main.yml'}],
                'message': message,
                'raw_node': revision,
                'node': revision,
                'utctimestamp': timestamp,
                'branch': 'master',
                'revlink': 'http://www.google.com',
            })

        payload = {
            'canon_url': 'https://bitbucket.org',
            'repository': {'absolute_url': '/scality/test', 'scm': 'git'},
            'commits': commits,
        }
        webhook_url = 'http://localhost:%d/change_hook/bitbucket'
        requests.post(webhook_url % (BASE_HTTP_PORT + master_id),
                      data={'payload': json.dumps(payload)})

    def get_bootstrap_builder(self, master_id=1):
        return self.api.get(
            'builders?name=bootstrap-master%d' % master_id)['builders'][0]

    def get_bootstrap_build(self, master_id=1, build_number=1):
        builder = self.get_bootstrap_builder(master_id)
        for _ in range(10):
            try:
                return self.api.get(
                    'builds?builderid=%d&number=%d' %
                    (builder['builderid'], build_number))['builds'][0]
            except IndexError:
                time.sleep(1)
                print('waiting for build to start')
        raise Exception('unable to find bootstrap build master_id=%d, '
                        'builderid=%d, build_number=%d' %
                        (master_id, builder['builderid'], build_number))

    def get_build_result(self, build_number=1, master_id=1,
                         expected_result='success'):
        for _ in range(60):
            build = self.get_bootstrap_build(master_id=master_id,
                                             build_number=build_number)
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
        self.notify_webhook(master_id=1)
        time.sleep(10)
        self.commit_git('ring')
        self.notify_webhook(master_id=2)
        self.get_build_result(master_id=1, expected_result='success')
        self.get_build_result(master_id=2, expected_result='success')

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

    @unittest.skipIf(platform.system() == 'Darwin', 'Does not work on Mac')
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
