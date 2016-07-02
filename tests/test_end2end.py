import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

import docker
import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

SUCCESS = 0
FAILURE = 2
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

ENV_VARS = [
    'GIT_REPO',
    'GIT_CERT_KEY_BASE64',
    'DOCKER_HOST',
    'DOCKER_CERT_PATH',
    'DOCKER_TLS_VERIFY',
    'EVE_LOGIN',
    'EVE_PWD',
]

for v in ENV_VARS:
    assert os.environ[v]

MASTER_FQDN = os.environ['DOCKER_HOST'].replace('tcp://', '').split(':')[0]
os.environ['MASTER_FQDN'] = MASTER_FQDN
API_BASE_URL = 'http://%s:8000/api/v2/' % MASTER_FQDN


def cmd(command, ignore_exception=False):
    log = ''
    print('\nCOMMAND : %s' % command)
    process = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        sys.stdout.write(' | ' + nextline)
        sys.stdout.flush()
        log += nextline

    print(u' L________')

    process.communicate()
    exitCode = process.returncode

    if exitCode == 0 or ignore_exception:
        return log
    raise subprocess.CalledProcessError(exitCode, command)


cmd('mkdir -p eve/docker_worker/docker_certs')
cmd('cp -vfp %s/* eve/docker_worker/docker_certs/' % os.environ[
    'DOCKER_CERT_PATH'])


class BuildbotDataAPi():
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
        }
        self.auth = HTTPBasicAuth(
            os.environ['EVE_LOGIN'],
            os.environ['EVE_PWD'])

    def post(self, route, method, params={}):
        data = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }
        res = requests.post(self.base_url + route, json=data,
                            headers=self.headers,
                            auth=self.auth)
        print res.json()
        res.raise_for_status()
        return res.json()

    def get(self, route):
        res = requests.get(self.base_url + route, headers=self.headers)
        res.raise_for_status()
        return res.json()

    def get_element_id_from_name(self, route, name, id_key, name_key='name'):
        elements = self.get(route)[route]
        for e in elements:
            if e[name_key] == name:
                _id = e[id_key]
                break
        else:
            raise Exception('element not found')
        return _id

    def force_build(self, builderid):
        params = {
            'builderid': str(builderid),
            'username': '',
            'reason': 'force build',
            'repository': '',
            'project': '',
            'branch': '',
            'revision': ''
        }
        self.post('forceschedulers/force-bootstrap', 'force', params=params)


class Docker:
    def __init__(self, tag):
        certp = os.environ['DOCKER_CERT_PATH']
        del os.environ['DOCKER_CERT_PATH']
        tls_config = docker.tls.TLSConfig(
            client_cert=(
                os.path.join(certp, 'cert.pem'),
                os.path.join(certp, 'key.pem')),
            ca_cert=os.path.join(certp, 'ca.pem')
        )
        self.client = docker.AutoVersionClient(
            base_url=os.environ['DOCKER_HOST'],
            tls=tls_config)
        resp = self.client.build(path='eve', tag=tag)
        self.check_output(resp)
        self.tag = tag

    def check_output(self, response):
        for line in response:
            line = json.loads(line)
            if 'error' in line:
                output = "ERROR: " + line['error']
                print output
                raise Exception(output)
            for line in line.get('stream', '').split('\n'):
                if line:
                    print line

    def rm(self, name, force=False):
        resp = self.client.remove_container(name, force=force)
        if resp:
            self.check_output(resp)

    def rm_all(self, force=False):
        for c in self.client.containers(all=True):
            container_name = c.get('Names')[0]
            if 'eve' not in container_name and 'build' not in container_name:
                continue
            print('Removing Container %s' % container_name)
            self.rm(c.get('Id'), force=force)

    def run(self, name):
        c = self.client.create_container(
            image=self.tag,
            environment=dict(os.environ),
            host_config=self.client.create_host_config(port_bindings={
                8000: 8000,
                9989: 9989}),
            name=name
        )
        resp = self.client.start(container=c.get('Id'))
        if resp:
            self.check_output(resp)

    def execute(self, name, command):
        e = self.client.exec_create(
            container=name,
            cmd=command,
        )
        return self.client.exec_start(exec_id=e)


class TestEnd2End(unittest.TestCase):
    def setup_buildbot(self):
        self.docker = Docker('eve')
        self.docker.rm_all(force=True)
        self.docker.run('eve')
        self.api = BuildbotDataAPi(API_BASE_URL)
        for i in range(10):
            try:
                print('checking buildbot\'s webserver response')
                builds = self.api.get('builds')
                assert builds['meta']['total'] == 0
                break
            except requests.ConnectionError:
                time.sleep(1)
            else:
                raise Exception('Could not connect to API')

    def setup_git(self, eve_dir):
        old_dir = os.getcwd()
        this_dir = os.path.dirname(os.path.abspath(__file__))

        os.chdir(tempfile.mkdtemp())
        cmd('git clone git@bitbucket.org:scality/test_buildbot.git')
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
        print self.docker.execute('eve', 'cat master/twistd.log')

    def get_build_status(self, build_id, timeout=120):
        state = None
        for i in range(timeout):

            time.sleep(1)
            log = self.docker.execute('eve', 'cat master/twistd.log')
            if 'Traceback (most recent call last):' in log:
                print log
                raise Exception('Found an Exception Traceback in twistd.log')
            try:
                build = self.api.get('builds/%d' % build_id)['builds'][0]
            except requests.HTTPError as e:
                print 'Build did not start yet. API responded: %s' % e.message
                continue
            state = build['state_string']
            print('API responded: BUILD STATE = %s' % state)
            if state not in ('starting', 'created'):
                break
        assert state == 'finished'
        return build['results']

    def test_git_poll_success_failure(self):
        self.setup_buildbot()
        self.setup_git('expected_fail')
        self.assertEqual(FAILURE, self.get_build_status(build_id=1))
        self.setup_git('four_stages_sleep')
        self.assertEqual(SUCCESS, self.get_build_status(build_id=2))

    def dtest_force_build(self):
        self.setup_git('four_stages_sleep')
        self.setup_buildbot()
        bootstrap_builder_id = self.api.get_element_id_from_name(
            'builders',
            'bootstrap',
            'builderid')
        self.api.force_build(bootstrap_builder_id)
        self.assertEqual(SUCCESS, self.get_build_status(build_id=1))
