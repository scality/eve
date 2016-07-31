# coding: utf-8
"""A thin layer above docker-py to simplify interaction with docker."""
import json
import logging
import os
import shutil
import tempfile

import docker

UNIX_SOCKET_URL = 'unix:///var/run/docker.sock'
UNIX_SOCKET_PATH = '/var/run/docker.sock'
logger = logging.getLogger(__name__)


class Docker(object):
    """A class barely representing a docker image instance."""

    def __init__(self, tag, docker_host, docker_cert_path):
        self.tag = tag
        if docker_cert_path:
            tls_config = docker.tls.TLSConfig(
                client_cert=(
                    os.path.join(docker_cert_path, 'cert.pem'),
                    os.path.join(docker_cert_path, 'key.pem')),
                ca_cert=os.path.join(docker_cert_path, 'ca.pem')
            )
        else:
            tls_config = None
        self.client = docker.AutoVersionClient(
            base_url=docker_host,
            tls=tls_config)

    def build_image(self, name, git_cert_path, master_docker_cert_path,
                    workers_docker_cert_path):
        """Build EVE docker image."""
        try:
            tmp_dir = tempfile.mkdtemp()
            docker_path = os.path.join(tmp_dir, name)
            shutil.copytree('master', docker_path)
            certs_dest = os.path.join(docker_path, 'certs')
            os.mkdir(certs_dest)
            shutil.copytree(git_cert_path, os.path.join(certs_dest, 'git'))
            if master_docker_cert_path:
                shutil.copytree(master_docker_cert_path,
                                os.path.join(certs_dest, 'docker_master'))
            if workers_docker_cert_path:
                shutil.copytree(workers_docker_cert_path,
                                os.path.join(certs_dest, 'docker_workers'))

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
        for output in response:
            for json_line in output.rstrip().split('\r\n'):
                formatted = json.loads(json_line)
                if 'error' in formatted:
                    raise Exception("ERROR: " + formatted['error'])
                if formatted:
                    for line in formatted['stream'].split('\n'):
                        if line:
                            logger.info(line)

    def remove(self, name, force=False):
        """Remove a docker instance, even if it is stopped."""
        self.client.remove_container(name, force=force)

    def rm_all(self, pattern, force=False):
        """Remove all docker instances whose names contain 'eve' or 'build'."""
        for container in self.client.containers(all=True):
            container_name = container.get('Names')[0]
            if pattern not in container_name:
                continue
            logger.info('Removing container %s as it contains the pattern %s',
                        container_name, pattern)
            self.remove(container.get('Id'), force=force)

    def run(self, name, env_vars, http_port, pb_port):
        """Run EVE in a docker instance."""
        if env_vars['DOCKER_HOST'] == UNIX_SOCKET_URL:
            volumes = [UNIX_SOCKET_PATH]
            binds = {
                UNIX_SOCKET_PATH: UNIX_SOCKET_PATH,
                # 'mode': 'rw',
            }
        else:
            volumes = []
            binds = {}
        container = self.client.create_container(
            hostname=name,
            name=name,
            image=self.tag,
            environment=env_vars,
            volumes=volumes,
            host_config=self.client.create_host_config(
                binds=binds,
                port_bindings={
                    8000: http_port,
                    9000: pb_port}),
        )
        cont_id = container.get('Id')
        self.client.start(container=cont_id)
        return cont_id

    def execute(self, name, command):
        """Execute a command into a running docker container."""
        handle = self.client.exec_create(
            container=name,
            cmd=command,
        )
        return self.client.exec_start(exec_id=handle)
