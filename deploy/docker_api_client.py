import json
import os
import shutil
import tempfile
from os.path import join

import docker


class Docker:

    def __init__(self, tag, docker_host, docker_cert_path, docker_use_tls):
        self.tag = tag
        tls_config = docker.tls.TLSConfig(
            client_cert=(
                os.path.join(docker_cert_path, 'cert.pem'),
                os.path.join(docker_cert_path, 'key.pem')),
            ca_cert=os.path.join(docker_cert_path, 'ca.pem')
        )
        self.client = docker.AutoVersionClient(
            base_url=docker_host,
            tls=tls_config)

    def build_image(self, worker_cert_path):
        d = tempfile.mkdtemp()
        docker_path = join(d, 'eve')
        shutil.copytree('eve/master', docker_path)
        shutil.copytree(worker_cert_path, join(docker_path,
                                               'worker_docker_certs'))
        resp = self.client.build(path=docker_path, tag=self.tag)
        self.check_output(resp)

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

    def run(self, name, env_vars={}):

        # cmd('mkdir -p eve/docker_worker/docker_certs')
        # cmd('cp -vfp %s/* eve/docker_worker/docker_certs/' %
        #    master_docker_cert_path)

        c = self.client.create_container(
            image=self.tag,
            environment=env_vars,
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
