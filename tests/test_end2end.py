import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

import requests

os.environ['GIT_REPO'] = 'git@bitbucket.org:scality/test_buildbot.git'


def cmd(command, ignore_exception=False):
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
    print(u' L________')

    output = process.communicate()[0]
    exitCode = process.returncode

    if exitCode == 0 or ignore_exception:
        return output
    raise subprocess.CalledProcessError(exitCode, command)


class BuildbotDataAPi():
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
        }

    def post(self, route, method, params={}):
        data = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }
        res = requests.post(self.base_url + route, json=data,
                            headers=self.headers)
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


class TestEnd2End(unittest.TestCase):

    def setup_buildbot(self):
        cmd('docker build -t eve eve')
        cmd('docker rm -f $(docker ps -aq)', ignore_exception=True)
        cmd('docker run -d -e GIT_REPO=%s ' % os.environ['GIT_REPO'] +
            '-p 8000:8000 -p 9989:9989 --name=eve eve')
        self.api = BuildbotDataAPi(
            'http://buildfaster.devsca.com:8000/api/v2/')
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

    def setup_git(self):
        c = 'four_stages_sleep'
        old_dir = os.getcwd()
        this_dir = os.path.dirname(os.path.abspath(__file__))
        src_ctxt = os.path.join(this_dir, 'contexts', c)
        os.chdir(tempfile.mkdtemp())
        cmd('git clone git@bitbucket.org:scality/test_buildbot.git')
        os.chdir('test_buildbot')

        shutil.rmtree('.buildbot')
        shutil.copytree(src_ctxt, '.buildbot')
        cmd('git config user.email "john.doe@example.com"')
        cmd('git config user.name "John Doe"')
        cmd('git config push.default simple')
        cmd('git add -A')
        cmd('git commit --allow-empty -m "changed build context to %s"' % c)
        cmd('git push')
        os.chdir(old_dir)

    def check_build_success(self, build_id, timeout=120):
        state = None
        for i in range(timeout):
            time.sleep(1)
            log = subprocess.check_output(
                'docker exec eve cat master/twistd.log', shell=True)
            if 'Traceback (most recent call last):' in log:
                cmd('docker exec eve cat master/twistd.log')
                raise Exception('Found an Exception Traceback in twistd.log')
            try:
                build = self.api.get('builds/%d' % build_id)['builds'][0]
            except requests.HTTPError as e:
                print 'Build did not start yet. API responded: %s' % e.message
                continue
            state = build['state_string']
            print('API responded: BUILD STATE = %s' % state)
            if state != 'starting':
                break
        assert state == 'finished'
        assert build['results'] == 0  # SUCCESS

    def test_git_poll(self):
        self.setup_buildbot()
        self.setup_git()
        self.check_build_success(build_id=1)

    def test_force_build(self):
        self.setup_git()
        self.setup_buildbot()
        bootstrap_builder_id = self.api.get_element_id_from_name(
            'builders',
            'bootstrap',
            'builderid')
        self.api.force_build(bootstrap_builder_id)
        self.check_build_success(build_id=1)
