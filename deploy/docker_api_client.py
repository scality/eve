# coding: utf-8
"""A thin layer above docker-py to simplify interaction with docker."""
import base64
import hashlib
import json
import logging
import os
import shutil
import tempfile

import docker
from jinja2 import Template

logger = logging.getLogger(__name__)


class Docker(object):
    """A class barely representing a docker image instance."""

    def __init__(self, tag, fqdn, login, pwd, docker_host, docker_cert_path):
        self.tag = tag
        self.fqdn = fqdn
        self.login = login
        self.pwd = pwd
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
        """Build EVE docker image."""
        try:
            tmp_dir = tempfile.mkdtemp()
            docker_path = os.path.join(tmp_dir, 'eve')
            shutil.copytree('eve/master', docker_path)
            shutil.copytree(worker_cert_path, os.path.join(
                docker_path,
                'worker_docker_certs'))
            shutil.copytree('etc', os.path.join(docker_path, 'etc'))

            # Generate reverse proxy config
            nginx_conf = os.path.join(docker_path, 'etc', 'nginx-eve.conf')
            with open(nginx_conf, 'w') as conf_file:
                template = Template(open(nginx_conf + '.j2', 'r').read())
                conf_file.write(template.render(fqdn=self.fqdn))

            # Generate htpasswd file
            htpasswd = os.path.join(docker_path, 'etc', 'htpasswd')
            with open(htpasswd, 'w') as conf_file:
                salt = os.urandom(4)
                sha1 = hashlib.sha1(self.pwd)
                sha1.update(salt)
                ssha = base64.b64encode(sha1.digest() + salt)
                template = Template(open(htpasswd + '.j2', 'r').read())
                conf_file.write(template.render(login=self.login, ssha=ssha))

            resp = self.client.build(path=docker_path, tag=self.tag)
            self.check_output(resp)
        finally:
            shutil.rmtree(tmp_dir)

    @staticmethod
    def check_output(response):
        """Check the output of a docker command.

        This method will raise an Exception if docker is reporting any
        error.
        """
        for line in response:
            line = json.loads(line)
            if 'error' in line:
                raise Exception("ERROR: " + line['error'])
            for line in line.get('stream', '').split('\n'):
                if line:
                    logger.info(line)

    def remove(self, name, force=False):
        """Remove a docker instance, even if it is stopped."""
        self.client.remove_container(name, force=force)

    def rm_all(self, force=False):
        """Remove all docker instances whose names contain 'eve' or 'build'."""
        for container in self.client.containers(all=True):
            container_name = container.get('Names')[0]
            if 'eve' not in container_name and 'build' not in container_name:
                continue
            logger.info('Removing Container %s', container_name)
            self.remove(container.get('Id'), force=force)

    def run(self, name, env_vars=None):
        """Run EVE in a docker instance."""
        container = self.client.create_container(
            image=self.tag,
            environment=env_vars,
            host_config=self.client.create_host_config(port_bindings={
                80: 80,
                443: 443,
                9989: 9989}),
            name=name
        )
        self.client.start(container=container.get('Id'))

    def execute(self, name, command):
        """Execute a command into a running docker container."""
        handle = self.client.exec_create(
            container=name,
            cmd=command,
        )
        return self.client.exec_start(exec_id=handle)
