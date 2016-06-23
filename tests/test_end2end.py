import os
import subprocess
import time
import tempfile
import unittest
from subprocess import check_output as cmd

import requests


def run_buildbot():
    try:
        cmd(['buildbot', 'stop', '/tmp/buildbot-master'])
        cmd(['rm', '-rf', '/tmp/buildbot-master'])
    except subprocess.CalledProcessError:
        pass
    cmd(['cp', '-r', 'buildbot', '/tmp/buildbot-master'])
    cmd(['mv', '/tmp/buildbot-master/master.cfg.py',
         '/tmp/buildbot-master/master.cfg'])
    cmd(['buildbot', 'create-master', '/tmp/buildbot-master'])

    cfg_file = '/tmp/buildbot-master/master.cfg'
    with open(cfg_file, "rb") as f:
        compile(f.read(), cfg_file, 'exec')

    try:
        cmd(['buildbot', 'start', '/tmp/buildbot-master'])
        return True
    except subprocess.CalledProcessError as e:
        with open('/tmp/buildbot-master/twistd.log') as logfile:
            print(logfile.read())
        print "output:\n", e.output
        raise


class BuildbotDataAPi():
    def __init__(self):
        self.base_url = 'http://localhost:8020/api/v2/'
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
        print params
        self.post('forceschedulers/force', 'force', params=params)


class TestEnd2End(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        cmd(['mkdir', d + '/.buildbot'])
        cmd(['cp', 'tests/success.yml', d + '/.buildbot/main.yaml'])
        old_dir = os.getcwd()
        os.chdir(d)
        cmd(['git', 'init'])
        cmd(['git', 'config', 'user.email', 'john@example.com'])
        cmd(['git', 'config', 'user.name', 'john'])
        cmd(['git', 'add', '.buildbot/main.yaml'])
        cmd(['git', 'commit', '-m', 'first commit'])
        os.environ['GIT_REPO'] = d
        os.chdir(old_dir)
        run_buildbot()
        self.api = BuildbotDataAPi()

    def test_run(self):
        bootstrap_builder_id = self.api.get_element_id_from_name(
            'builders',
            'b-bootstrap',
            'builderid')
        self.api.force_build(bootstrap_builder_id)
        for i in range(120):
            time.sleep(1)
            build = self.api.get('builds/1')['builds'][0]
            state = build['state_string']
            print state
            if state != 'starting':
                break
        assert state == 'finished'
        assert build['results'] == 0  # SUCCESS

class TestUnit(unittest.TestCase):
    def test_docker(self):
        with open('tests/Dockerfile.template') as f:
            dockerfile = f.read().format(
                master_hostname='192.168.99.1',
                workername='latent-docker-worker-1',
                workerpassword='pwd'
            )

        with open('tests/Dockerfile', 'w') as f:
            f.write(dockerfile)

        #cmd(['docker', 'build', '--tag', 'latent-docker-worker-1', 'tests'])
        import docker
        from os import path
        CERTS = path.join(path.expanduser('~'), '.docker', 'machine', 'machines', 'default')
        tls_config = docker.tls.TLSConfig(
            client_cert=(path.join(CERTS, 'cert.pem'), path.join(CERTS,'key.pem')),
            ca_cert=path.join(CERTS, 'ca.pem'),
            verify=True
        )

        docker_socket = 'tcp://192.168.99.100:2376'
        client = docker.client.Client(base_url=docker_socket, tls=tls_config)
        worker_image= 'latent-docker-worker-1'
        container = client.create_container(worker_image)
        client.start(container['Id'])
        client.stop(container['Id'])
        client.wait(container['Id'])

