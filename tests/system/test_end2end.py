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

import eve
import requests
import yaml
from buildbot.process.results import FAILURE, SUCCESS, WARNINGS

from dotenv import load_dotenv

from .buildbot_api_client import BuildbotDataAPI
from .cmd import cmd
from .codecov_io_server import CodecovIOMockServer

__dirpath__ = os.path.dirname(__file__)
"""Path of this directory (used to locate file in a docker context)."""

__evedir__ = os.path.dirname(eve.__file__)
"""Path to the module of eve (contains services, master config file, ...)."""


logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logging.getLogger('requests').setLevel(logging.WARNING)

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning)

BASE_TRY_PORT = 7990
BASE_HTTP_PORT = 8990
BASE_PB_PORT = 9990
WAMP_PORT = 10990


def need_env_vars(varnames, reason):
    """Decorator to skip test if environment variables are not passsed."""
    return unittest.skipIf(
        any([
            varname not in os.environ
            for varname in varnames
        ]),
        reason
    )


def need_rackspace_credentials(reason='needs rackspace credentials'):
    """Decorator to skip test if rackspace credentials are not passed."""
    return need_env_vars([
        'RAX_LOGIN', 'RAX_PWD'
    ], reason)


def need_artifacts_credentials(reason='needs artifacts credentials'):
    """Decorator to skip test if artifacts credentials are not passed."""
    return need_env_vars([
        'ARTIFACTS_URL',
        'SECRET_ARTIFACT_CREDS'
    ], reason)


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


def setup_local_job(masterdir, job_files):
    if job_files is None:
        # allow creation of directory for ""
        return
    local_dirpath = os.path.join(
        masterdir, os.environ.get('LOCAL_JOBS_DIRPATH', 'local'))
    shutil.rmtree(local_dirpath, ignore_errors=True)
    cmd('mkdir -p %s' % local_dirpath)
    if not job_files:
        return

    os.chdir(local_dirpath)
    if isinstance(job_files, list):
        for job in job_files:
            job_yaml_file = os.path.join(
                __dirpath__, 'local', '%s.yml' % job)
            cmd('cp -r %s .' % job_yaml_file)
    else:
        job_yaml_file = os.path.join(
            __dirpath__, 'local', '%s.yml' % job_files)
        cmd('cp -r %s .' % job_yaml_file)
    os.chdir(masterdir)


class BaseTest(unittest.TestCase):  # pylint: disable=too-many-public-methods
    """Base class for test classes

    - Sets-up bitbucket git repo
    - Checks build status
    """

    webhook_url = 'http://localhost:%d/change_hook/bitbucket'
    api = None
    eve = None

    def setUp(self):
        dotenv_path = os.path.join(os.path.dirname(__file__), 'test_env')
        load_dotenv(dotenv_path)
        # Set extra environment variables
        test_method = getattr(self, self._testMethodName)
        extra_environ = getattr(test_method, "__eve_environ__", False)
        frontend_jobs = getattr(test_method, "__frontend_jobs__", None)
        backend_jobs = getattr(test_method, "__backend_jobs__", None)
        if extra_environ:
            for varname, value in extra_environ.iteritems():
                test_method.__old_eve_environ__.update({
                    varname: os.environ.get(varname)
                })
                os.environ[varname] = str(value)

        self.master_fqdn = os.getenv('MASTER_FQDN', 'auto')
        if self.master_fqdn == 'auto':
            self.master_fqdn = get_master_fqdn()

        tmpdir = os.getenv('WORKDIR', '/tmp/eve_tests')
        self.test_dir = os.path.join(tmpdir, 'test_eve')
        try:
            self.shutdown_eve()
        except OSError:
            pass
        cmd('mkdir -p %s' % self.test_dir)
        self.git_dir = tempfile.mkdtemp(
            prefix=os.path.join(tmpdir, 'eve_repo_'))
        self.url = 'http://%s:%d/' % (self.master_fqdn, BASE_HTTP_PORT)
        os.environ['EXTERNAL_URL'] = self.url
        self.setup_crossbar()
        self.setup_eve_master_frontend(master_id=0, local_jobs=frontend_jobs)
        self.setup_eve_master_backend(master_id=1, local_jobs=backend_jobs)
        self.setup_eve_master_backend(master_id=2)
        self.api = BuildbotDataAPI(self.url)
        self.api.login("eve", "eve")

        self.setup_git()

    def tearDown(self):
        # Restore extra environment variables
        test_method = getattr(self, self._testMethodName)
        old_environ = getattr(test_method, "__old_eve_environ__", False)
        if old_environ:
            for varname, value in old_environ.iteritems():
                if value is not None:
                    os.environ[varname] = value
                else:
                    del os.environ[varname]

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

    def setup_eve_master_frontend(self, master_id, local_jobs=None):
        """Spawns a EVE master frontend.

        It will wait until it is up and running.
        """
        os.environ['TRY_PORT'] = str(BASE_TRY_PORT + master_id)
        os.environ['HTTP_PORT'] = str(BASE_HTTP_PORT + master_id)
        os.environ['MASTER_FQDN'] = self.master_fqdn
        os.environ['SUFFIX'] = 'test-eve%d' % master_id
        os.environ['PB_PORT'] = str(BASE_PB_PORT + master_id)
        os.environ['MAX_LOCAL_WORKERS'] = '1'
        self.setup_eve_master(
            master_id, master_mode='frontend', local_jobs=local_jobs)

    def setup_eve_master_backend(self, master_id, local_jobs=None):
        """Spawns a EVE master backend.

        It will wait until it is up and running.
        """
        os.environ['MASTER_FQDN'] = self.master_fqdn
        os.environ['SUFFIX'] = 'test-eve%d' % master_id

        os.environ['PB_PORT'] = str(BASE_PB_PORT + master_id)
        os.environ['MAX_LOCAL_WORKERS'] = '1'
        self.setup_eve_master(
            master_id, master_mode='backend', local_jobs=local_jobs)

    def setup_eve_master(self, master_id, master_mode, local_jobs=None):
        """Spawns a EVE master backend.

        It will wait until it is up and running.
        """
        os.environ['MASTER_MODE'] = master_mode
        sql_path = os.path.join(self.test_dir, 'state.sqlite')
        os.environ['DB_URL'] = 'sqlite:///' + sql_path

        os.environ['WAMP_ROUTER_URL'] = 'ws://localhost:%d/ws' % WAMP_PORT
        os.environ['WAMP_REALM'] = 'buildbot'

        master_cfg = os.path.join(__evedir__, 'etc', 'master.cfg')

        masterdir = os.path.join(self.test_dir, 'master%i' % master_id)
        cmd('mkdir -p %s' % masterdir)
        os.chdir(masterdir)
        cmd('cp %s .' % master_cfg)

        setup_local_job(masterdir, local_jobs)

        cmd('buildbot create-master --relocatable --db=%s .' %
            os.environ['DB_URL'])

        cmd('buildbot start .')

    def setup_crossbar(self):
        """Spawns a local crossbar.
        """
        crossbar_dir = os.path.join(self.test_dir, 'crossbar')
        cmd('mkdir -p %s' % crossbar_dir)
        crossbar_cfg_path = os.path.join(
            __dirpath__, 'crossbar.json')
        os.chdir(crossbar_dir)

        cmd('cp %s %s' % (crossbar_cfg_path,
                          os.path.join(crossbar_dir, 'config.json')))
        cmd('crossbar start --logtofile --cbdir %s' % crossbar_dir, wait=False)

    def setup_git(self):
        """Create a new git repo."""

        builddir = os.path.join(__evedir__, 'services/git_cache')
        cmd('docker build -t git_cache %s' % builddir)
        cmd('docker rm -f git_cache', ignore_exception=True)
        cmd('docker run -d -p 2222:80 --name git_cache git_cache')
        time.sleep(3)  # wait for cache service to stabilize

        cmd('mkdir -p %s' % self.git_dir)
        os.chdir(self.git_dir)
        cmd('git clone http://localhost:2222/mock/test_owner/mock.git .')

        cmd('git config user.email "john.doe@example.com"')
        cmd('git config user.name "John Doe"')
        cmd('git config push.default simple')
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
        src_ctxt = os.path.join(__dirpath__, 'contexts')
        shutil.rmtree('eve', ignore_errors=True)
        shutil.copytree(src_ctxt, 'eve')
        eve_yaml_file = os.path.join(
            __dirpath__, 'yaml', eve_dir, 'main.yml')
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
                        'href': 'https://mock/test_owner/mock'
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

    def get_builder(self, name):
        """Get builder named name from the Buildbot's API."""
        return self.api.get('builders?name=%s' % name)['builders'][0]

    def get_scheduler(self, name):
        """Get scheduler named name from the Buildbot's API."""
        return self.api.get('schedulers?name=%s' % name)['schedulers'][0]

    def get_build(self, builder='test_boostrap', build_number=1):
        """Wait for build to start and return its infos."""
        builder = self.get_builder(builder)
        for _ in range(10):
            try:
                return self.api.get(
                    'builds?builderid=%d&number=%d' %
                    (builder['builderid'], build_number))['builds'][0]
            except IndexError:
                time.sleep(1)
                print('waiting for build to start')
        raise Exception('unable to find build, '
                        'builderid=%d, build_number=%d' %
                        (builder['builderid'], build_number))

    def get_build_steps(self, builder='test_bootstrap', build_number=1):
        """Returns steps from specified builder and build."""
        builder = self.get_builder(builder)
        try:
            return self.api.get(
                'builders/%d/builds/%d/steps' %
                (builder['builderid'], build_number))['steps']
        except KeyError:
            raise Exception('unable to find build steps, '
                            'builderid=%d, build_number=%d' %
                            (builder['builderid'], build_number))

    def get_step(self, name, builder='test_bootstrap', build_number=1):
        """Returns matching step from specified builder and build number."""
        steps = self.get_build_steps(
            builder=builder, build_number=build_number)
        step = [s for s in steps if s["name"] == name]
        if not step:
            raise Exception('unable to find build step %r, '
                            'builderid=%d, build_number=%d' %
                            (name, builder['builderid'], build_number))
        return step[0]

    def get_build_result(self, builder='test_bootstrap', build_number=1,
                         expected_result='success'):
        """Get the result of the build `build_number`."""
        for _ in range(900):
            build = self.get_build(builder=builder, build_number=build_number)
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


class Test(BaseTest):  # pylint: disable=too-many-public-methods

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

        steps = self.get_build_steps()
        assert (steps[-2]['name'] == 'build docker image from '
                                     'eve/bad-ubuntu-trusty-ctxt')
        assert (steps[-1]['name'] == 'docker build retry from '
                                     'eve/bad-ubuntu-trusty-ctxt')

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

    @need_rackspace_credentials()
    @need_artifacts_credentials()
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

    @unittest.skip('Test flaky on developer''s machine '
                   'which need to be investigated and fixed.')
    def test_lost_slave_recovery(self):
        """Ensures test can recover when slave is lost.

        Steps :
         * Launch the first job, that kills buildbot/container
         * The build shouldn't be retried and should fail
        """
        self.commit_git('lost_slave_recovery')
        self.notify_webhook()
        self.get_build_result(expected_result='failure')

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

    def test_use_premade_docker_img(self):
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

    def test_use_premade_docker_img_p(self):
        """Same test than test_use_premade_docker_image but use
        property to store the image id."""
        self.commit_git('use_premade_docker_image_property')
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

    @unittest.skip('Really slow (5 minutes)')
    def test_use_broken_openstack(self):
        """Test the retry mechanism when OpenStack spawning fails.

        Steps:
         * Substantiate an openstack worker with an inexisting image and no
         credentials
         * Expect a failure after 5 minutes or so
        """
        self.commit_git('use_broken_openstack')
        self.notify_webhook()
        self.get_build_result(expected_result='failure')

    @use_environ(FOO="BAR")
    def test_worker_environ(self):
        """Test worker environment.

        Steps:
        * Spawn worker
        * Check Eve environment variables are not setted in the worker
        """
        self.commit_git('worker_environ')
        self.notify_webhook()
        self.get_build_result(expected_result='success')

    def test_junit_step(self):  # pylint: disable=too-many-statements
        """Test customized JUnitShellCommand step with OK tests.

        Steps:
        * Spawn worker
        * Have various commands create JUnit reports and parse them
        """
        self.commit_git('junit_step')
        self.notify_webhook()
        self.get_build_result(expected_result='failure')

        # crude method to determine which builder executed the steps
        builder = 'test_docker_builder-test-eve1'
        try:
            step = self.get_step(
                name=u'single report with one pass', builder=builder)
        except:  # pylint: disable=bare-except
            builder = 'test_docker_builder-test-eve2'
            step = self.get_step(
                name=u'single report with one pass', builder=builder)

        assert step['results'] == SUCCESS
        assert step['state_string'] == u'T:1 E:0 F:0 S:0'

        step = self.get_step(
            name=u'three reports with lots of pass', builder=builder)
        assert step['results'] == SUCCESS
        assert step['state_string'] == u'T:2134 E:0 F:0 S:108'

        step = self.get_step(
            name=u'no files in directory', builder=builder)
        assert step['results'] == WARNINGS
        assert step['state_string'] == u'no test results found'

        step = self.get_step(
            name=u'missing report directory', builder=builder)
        assert step['results'] == WARNINGS
        assert step['state_string'] == u'no test results found'

        step = self.get_step(
            name=u'single report with invalid data', builder=builder)
        assert step['results'] == WARNINGS
        assert step['state_string'] == u'no test results found'

        step = self.get_step(
            name=u'report with invalid data along valid report',
            builder=builder)
        assert step['results'] == SUCCESS
        assert step['state_string'] == u'T:1 E:0 F:0 S:0'

        step = self.get_step(
            name=u'single report with invalid extension', builder=builder)
        assert step['results'] == WARNINGS
        assert step['state_string'] == u'no test results found'

        step = self.get_step(
            name=u'report with failures and successful command',
            builder=builder)
        assert step['results'] == FAILURE
        assert (step['state_string'] ==
                u'FAIL: toto.tests.sample.test_sample.test_sample')

        step = self.get_step(
            name=u'report with no failures and failed command',
            builder=builder)
        assert step['results'] == FAILURE
        assert step['state_string'] == u'T:1 E:0 F:0 S:0'

        step = self.get_step(name=u'report with failures', builder=builder)
        assert step['results'] == FAILURE
        assert (step['state_string'] ==
                u'FAIL: toto.tests.sample.test_sample.test_sample')

        step = self.get_step(name=u'report with errors', builder=builder)
        assert step['results'] == FAILURE
        assert (step['state_string'] ==
                u'ERROR: supervisor.test_01_deployment.TestGenericDeployment.'
                'test_supervisor_configuration[os_trusty]')

        step = self.get_step(name=u'report with skips', builder=builder)
        assert step['results'] == SUCCESS
        assert step['state_string'] == u'T:144 E:0 F:0 S:24'

        step = self.get_step(
            name=u'report with both errors and failures',
            builder=builder)
        assert step['results'] == FAILURE
        assert (step['state_string'] ==
                u'ERROR: supervisor.test_01_deployment.TestGenericDeployment.'
                'test_supervisor_configuration[os_trusty]')

        step = self.get_step(
            name=u'report with one xfail and one xpass', builder=builder)
        assert step['results'] == SUCCESS
        assert step['state_string'] == u'T:2 E:0 F:0 S:2'

        step = self.get_step(
            name=u'undeclared report directory and a pass', builder=builder)
        assert step['results'] == WARNINGS
        assert step['state_string'] == u'no test results found'

        step = self.get_step(
            name=u'undeclared report directory and a fail', builder=builder)
        assert step['results'] == FAILURE
        assert step['state_string'] == u'no test results found'

    @frontend_local_job("periodic")
    @use_environ(LOCAL_JOBS_DIRPATH="local2/sub")
    def test_local_job_frontend(self):
        """Test a local job on the frontend.

        The local directory is customized with a subdirectory.

        Steps:
        * Configure local job in decorator
        * Check Eve can start (no error in setup)
        * Verify directories and files (test setup validation)
        * Check schedulers and builders are correct
        """
        try:
            path = os.path.join(self.test_dir, 'master0/local2/sub')
            assert os.path.isdir(path)
            path = os.path.join(
                self.test_dir, 'master0/local2/sub/periodic.yml')
            assert os.path.isfile(path)
            path = os.path.join(self.test_dir, 'master1/local2/sub')
            assert not os.path.isdir(path)
            path = os.path.join(
                self.test_dir, 'master1/local2/sub/periodic.yml')
            assert not os.path.isfile(path)

            builder = self.get_builder('my-periodic-builder')
            assert builder['description'] == 'I run periodically'
            scheduler = self.get_scheduler('my-periodic-scheduler')
            assert 'master0' in scheduler['master']['name']
            time.sleep(5)  # let job trigger at least once
            step = self.get_step(
                name=u'type something on console',
                builder=str(builder['name']))
            assert step['results'] == SUCCESS
        finally:
            # stop eve manually to prevent periodic job from running
            self.shutdown_eve()

    @backend_local_job("periodic")
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
        try:
            path = os.path.join(self.test_dir, 'master0/local')
            assert not os.path.isdir(path)
            path = os.path.join(self.test_dir, 'master0/local/periodic.yml')
            assert not os.path.isfile(path)
            path = os.path.join(self.test_dir, 'master1/local')
            assert os.path.isdir(path)
            path = os.path.join(self.test_dir, 'master1/local/periodic.yml')
            assert os.path.isfile(path)

            builder = self.get_builder('my-periodic-builder')
            assert builder['description'] == 'I run periodically'
            scheduler = self.get_scheduler('my-periodic-scheduler')
            assert 'master1' in scheduler['master']['name']
            time.sleep(5)  # let job trigger at least once
            step = self.get_step(
                name=u'type something on console',
                builder=str(builder['name']))
            assert step['results'] == SUCCESS
        finally:
            # stop eve manually to prevent periodic job from running
            self.shutdown_eve()

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
        try:
            path = os.path.join(self.test_dir, 'master0/local')
            assert os.path.isdir(path)
            path = os.path.join(self.test_dir, 'master0/local/periodic.yml')
            assert os.path.isfile(path)
            path = os.path.join(self.test_dir, 'master0/local/nightly.yml')
            assert os.path.isfile(path)
            path = os.path.join(self.test_dir, 'master1/local')
            assert os.path.isdir(path)
            path = os.path.join(self.test_dir, 'master1/local/nightly.yml')
            assert os.path.isfile(path)

            self.get_builder('my-periodic-builder')
            scheduler = self.get_scheduler('my-periodic-scheduler')
            assert 'master0' in scheduler['master']['name']
            scheduler = self.get_scheduler('nightly-scheduler-test-eve0')
            assert 'master0' in scheduler['master']['name']
            scheduler = self.get_scheduler('nightly-scheduler-test-eve1')
            assert 'master1' in scheduler['master']['name']
        finally:
            # stop eve manually to prevent periodic job from running
            self.shutdown_eve()

    @backend_local_job("")
    @use_environ(LOCAL_JOBS_DIRPATH="/tmp/.eve_test_data/local")
    def test_local_job_empty(self):  # pylint: disable=no-self-use
        """Test local jobs with no job defined and absolute path.

        (useful for people who want to store job files in /etc)

        Steps:
        * Configure local jobs in decorator
        * Check Eve can start (no error in setup)
        * Verify directory (test setup validation)
        """
        assert os.path.isdir('/tmp/.eve_test_data/local')

    def test_docker_build_label(self):
        """Test label on docker image exists."""
        self.commit_git('docker_build_label')
        self.notify_webhook()
        self.get_build_result(expected_result='success')


class TestPublishCodeCoverage(BaseTest):
    """Test code coverage report publication step.

    ``PublishCodeCoverage`` is the generic buildbot step to use to
    publish several code coverage reports to an external service.
    At this moment, only ``codecov.io`` service is supported.

    These tests are two operating modes:

    - The first is to use an internal mock ``codecov.io`` server.
    - The second use the real ``codecov.io`` service.

    By default, in the automatic tests, we use the mock ``codecov.io``
    server to avoid being dependent external services that could not
    be available in the future.

    To use the real ``codecov.io`` server, we need to define the
    environment variable **CODECOV_IO_UPLOAD_TOKEN** which is the
    ``codecov.io`` upload token of the repository given in
    *yaml/generate_coverage_report/main.yml* YAML file.
    """

    def __init__(self, *args, **kwargs):
        super(TestPublishCodeCoverage, self).__init__(*args, **kwargs)

        self.codecov_io_server = None

    def setUp(self):
        """Instantiate a ``codecov.io`` mock HTTP server if needed.

        We define the **CODECOV_IO_BASE_URL** environment variable to
        communicate with our mock HTTP server rather than the real
        ``codecov.io`` server (see
        `~master/steps/publish_coverage_report`).

        We define the **CODECOV_IO_UPLOAD_TOKEN** environment variable
        to avoid to skip the step.  It's the default behaviour if we
        don't give this variable to Eve.
        """
        if not os.environ.get('CODECOV_IO_UPLOAD_TOKEN'):
            self.codecov_io_server = CodecovIOMockServer('127.0.0.1')
            self.codecov_io_server.start()

            os.environ.update({
                'CODECOV_IO_BASE_URL': self.codecov_io_server.url,
                'CODECOV_IO_UPLOAD_TOKEN': 'FAKE_TOKEN',
            })

        super(TestPublishCodeCoverage, self).setUp()

    def tearDown(self):
        """Stop the ``codecov.io`` mock HTTP server if needed.

        And restore old environment variables.
        """
        super(TestPublishCodeCoverage, self).tearDown()

        if self.codecov_io_server:
            self.codecov_io_server.stop()
            self.codecov_io_server = None

        for varname_suffix in ['BASE_URL', 'UPLOAD_TOKEN']:
            varname = 'CODECOV_IO_{0}'.format(varname_suffix)
            if varname in os.environ:
                del os.environ[varname]

    def _get_publish_codecov_build(self, builder_name="test_docker_builder"):
        """Search the build of the code coverage report publication step.

        :args builder_name: Root builder name rather than bootstrap.
        :returns None: If we don't find the potential build.
        """
        builders = self.api.get(
            'builders?name__contains={0}'.format(builder_name)
        )
        for builder in builders['builders']:
            builds_url = "builders/{0}/builds".format(builder['builderid'])
            builds = self.api.get(builds_url)
            for build in builds['builds']:
                steps = self.api.get(
                    "{0}/{1}/steps?name__contains=coverage".format(
                        builds_url, build['number']
                    )
                )
                if steps:
                    return build
        return None

    def test_publication_success(self, name='generate_coverage_report'):
        """Test PublishCoverageReport success.

        :args name: Name of the directory which contains the
                      ``main.yml`` to commit.

        If we use the mock HTTP server, we ensure that we execute the
        requests with the correct query parameters and headers, in
        accordance with the ``codecov.io`` API (see
        https://docs.codecov.io/v4.3.0/reference#upload).
        """
        self.commit_git(name)
        self.notify_webhook()
        self.get_build_result(expected_result='success')

        if not self.codecov_io_server:
            return

        build = self._get_publish_codecov_build()
        assert build is not None, \
            'Unable to get the build which publish the code coverage report'

        report_filepath = os.path.join(
            __dirpath__, 'contexts', 'coverage-reports',
            'reports', 'coverage.xml'
        )

        yaml_filepath = os.path.join(__dirpath__, 'yaml', name, 'main.yml')
        with open(yaml_filepath, 'r') as yaml_file:
            yaml_content = yaml.load(yaml_file)

        try:
            steps = yaml_content['stages']['coverage_tests']['steps']
            publish_args = steps[1]['PublishCoverageReport']
        except (TypeError, KeyError):
            raise AssertionError(
                'Unable to get parameters of the PublishCoverageReport step'
            )

        self.codecov_io_server.assert_request_received_with((
            'POST', '/upload/v4', {
                'commit': publish_args['revision'],
                'token': 'FAKE_TOKEN',
                'build': 1,
                'build_url': '{0}#builders/{1}/builds/{2}'.format(
                    self.url, build['builderid'], build['number']
                ),
                'service': 'buildbot',
                'branch': publish_args['branch'],
                'name': publish_args['uploadName'],
                'slug': publish_args['repository'],
            }, {
                'Accept': 'text/plain',
            }
        ), (
            'PUT', '/s3/fake_report.txt', {
                'AWSAccessKeyId': 'FAKEAWSACCESSKID',
                'Expires': str(self.codecov_io_server.expires),
                'Signature': 'FAKESIGNATURE',
            }, {
                'Content-Length': str(os.path.getsize(report_filepath)),
                'Content-Type': 'text/plain',
                'x-amz-acl': 'public-read',
                'x-amz-storage-class': 'REDUCED_REDUNDANCY',
            }
        ))
