#coding: utf-8
"""A thin layer above docker-py to simplify interaction with docker"""
from __future__ import print_function

import json
import os
import shutil
import tempfile

import docker


class Docker(object):
    """A class barely representing a docker image instance"""

    def __init__(self, tag, docker_host, docker_cert_path):
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
        """Build EVE docker image"""
        try:
            docker_path = os.path.join(tempfile.mkdtemp(), 'eve')
            shutil.copytree('eve/master', docker_path)
            shutil.copytree(worker_cert_path, os.path.join(
                docker_path,
                'worker_docker_certs'))
            resp = self.client.build(path=docker_path, tag=self.tag)
            self.check_output(resp)
        finally:
            shutil.rmtree(docker_path)

    @staticmethod
    def check_output(response):
        """Check the output of a docker command and raise exception if docker
        is reporting errors"""
        for line in response:
            line = json.loads(line)
            if 'error' in line:
                raise Exception("ERROR: " + line['error'])
            for line in line.get('stream', '').split('\n'):
                if line:
                    print(line)

    def remove(self, name, force=False):
        """Remove a docker instance, even if it is stopped"""
        resp = self.client.remove_container(name, force=force)
        if resp:
            self.check_output(resp)

    def rm_all(self, force=False):
        """Remove all docker instances whose names contain 'eve' or 'build'"""
        for container in self.client.containers(all=True):
            container_name = container.get('Names')[0]
            if 'eve' not in container_name and 'build' not in container_name:
                continue
            print('Removing Container %s' % container_name)
            self.remove(container.get('Id'), force=force)

    def run(self, name, env_vars=None):
        """Run EVE in a docker instance"""
        container = self.client.create_container(
            image=self.tag,
            environment=env_vars,
            host_config=self.client.create_host_config(port_bindings={
                8000: 8000,
                9989: 9989}),
            name=name
        )
        resp = self.client.start(container=container.get('Id'))
        if resp:
            self.check_output(resp)

    def execute(self, name, command):
        """Execute a command into a running docker container"""
        handle = self.client.exec_create(
            container=name,
            cmd=command,
        )
        return self.client.exec_start(exec_id=handle)
