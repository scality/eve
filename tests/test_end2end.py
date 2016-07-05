#coding: utf-8
"""This test suite checks end-to-end operation of EVE"""
from __future__ import print_function

import os
import shutil
import tempfile
import time
import unittest

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from deploy.cmd import cmd
from deploy.deploy_eve_master import EveMaster

SUCCESS = 0
FAILURE = 2
EVE_WEB_LOGIN = 'test'
EVE_WEB_PWD = 'testpwd'
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class TestEnd2End(unittest.TestCase):
    """Tests the whole loop including bitbucket and the docker provider"""
    git_repo = 'git@bitbucket.org:scality/test_buildbot.git'
    eve = None

    def setup_eve_master(self):
        """Spawns a EVE docker master and wait for it till it
        is up and running"""

        docker_host = os.environ['DOCKER_HOST']
        master_fqdn = docker_host.replace('tcp://', '').split(':')[0]

        self.eve = EveMaster(
            bitbucket_git_repo=self.git_repo,
            bitbucket_git_cert_key_baser64=os.environ['GIT_CERT_KEY_BASE64'],
            master_fqdn=master_fqdn,

            worker_docker_host=os.environ['DOCKER_HOST'],
        )
        self.eve.set_bitbucket_credentials(
            os.environ['EVE_BITBUCKET_LOGIN'],
            os.environ['EVE_BITBUCKET_PWD'])
        self.eve.set_web_credentials(EVE_WEB_LOGIN, EVE_WEB_PWD)
        self.eve.deploy(
            master_docker_host=os.environ['DOCKER_HOST'],
            master_docker_cert_path=os.environ['DOCKER_CERT_PATH'],
            worker_docker_cert_path=os.environ['DOCKER_CERT_PATH']
        )
        self.eve.wait()

    def setup_git(self, eve_dir):
        """push the yaml file and the docker context to bitbucket"""
        old_dir = os.getcwd()
        this_dir = os.path.dirname(os.path.abspath(__file__))

        os.chdir(tempfile.mkdtemp())
        cmd('git clone %s' % self.git_repo)
        os.chdir('test_buildbot')

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

    def tearDown(self):
        """Writes the contents of twistd.log after every test"""
        if not hasattr(self.eve, 'docker'):
            return
        print(self.eve.docker.execute('eve', 'cat master/twistd.log'))

    def get_build_status(self, build_id, timeout=120):
        """Wait for the build to finish and get build status from buildbot.
        build statuses described in
        http://docs.buildbot.net/latest/developer/results.html"""
        state = None
        for _ in range(timeout):
            time.sleep(1)
            log = self.eve.docker.execute('eve', 'cat master/twistd.log')
            if 'Traceback (most recent call last):' in log:
                print(log)
                raise Exception('Found an Exception Traceback in twistd.log')
            try:
                build = self.eve.api.get('builds/%d' % build_id)['builds'][0]
            except requests.HTTPError as exp:
                print('Build did not start yet. API responded: %s' %
                      exp.message)
                continue
            state = build['state_string']
            print('API responded: BUILD STATE = %s' % state)
            if state not in ('starting', 'created'):
                break
        assert state == 'finished'
        # Bitbucket API bug. Happens sometimes!
        assert build['results'] is not None, 'finished but no results => bug'
        return build['results']

    def test_git_poll_success_failure(self):
        """Spawns EVE, sends a YAML that will fail and check that it fails.
        Then, sends a good YAML with 3 steps (with parallelization) and
        checks that it succeeds"""
        self.setup_eve_master()
        self.setup_git('expected_fail')
        self.assertEqual(FAILURE, self.get_build_status(build_id=1))
        self.setup_git('four_stages_sleep')
        self.assertEqual(SUCCESS, self.get_build_status(build_id=2))

    def test_force_build(self):
        """Sets up a git, Forces a build and check that it succeeds"""
        self.setup_git('four_stages_sleep')
        self.setup_eve_master()
        bootstrap_builder_id = self.eve.api.get_element_id_from_name(
            'builders',
            'bootstrap',
            'builderid')
        self.eve.api.force_build(bootstrap_builder_id, self.git_repo)
        self.assertEqual(SUCCESS, self.get_build_status(build_id=1))
