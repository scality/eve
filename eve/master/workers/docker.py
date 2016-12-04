"""Allow eve to use docker workers."""

from json import loads
from os import environ
from subprocess import STDOUT, CalledProcessError, check_output
import time

from buildbot.process.properties import Property
from buildbot.worker.docker import DockerLatentWorker
import netifaces
from twisted.internet import defer, threads
from twisted.logger import Logger


class EveDockerLatentWorker(DockerLatentWorker):
    """Improved version of DockerLatentWorker using the docker command line
     client instead of docker-py which was the cause of multiple dead locks
    """
    logger = Logger('eve.workers.EveDockerLatentWorker')

    def __init__(self, docker_tls_verify=None, docker_cert_path=None, **kw):
        self.docker_tls_verify = docker_tls_verify
        self.docker_cert_path = docker_cert_path
        self.docker_host = kw['docker_host']
        DockerLatentWorker.__init__(self, **kw)

    @defer.inlineCallbacks
    def start_instance(self, build):
        if self.instance is not None:
            raise ValueError('instance active')
        image = yield build.render(self.image)
        volumes = build.getProperty('docker_volumes')
        buildnumber = yield build.render(Property('buildnumber'))
        res = yield threads.deferToThread(self._thd_start_instance, image, volumes, buildnumber)
        defer.returnValue(res)

    def _thd_start_instance(self, image, volumes, buildnumber):
        if image not in self.docker_invoke('images'):
            # hack to avoid a loop when the original image does not exist
            self.docker_invoke('pull', 'ubuntu:trusty')
            image = 'ubuntu:trusty'

        docker_host_ip = None
        try:
            docker_addresses = netifaces.ifaddresses('docker0')
        except ValueError:
            pass
        else:
            try:
                docker_host_ip = docker_addresses[netifaces.AF_INET][0]['addr']
            except KeyError:
                pass

        cmd = [
            'run',
            '--privileged',
            '--env', 'BUILDMASTER=%s' % self.masterFQDN,
            '--env', 'WORKERNAME=%s' % self.name,
            '--env', 'WORKERPASS=%s' % self.password,
            '--env', 'BUILDMASTER_PORT=%s' % environ['PB_PORT'],
            '--env', 'DOCKER_HOST_IP=%s' % docker_host_ip,
            '--env', 'ARTIFACTS_PREFIX=%s' % environ.get('ARTIFACTS_PREFIX',
                                                         'staging-'),
            '--link', 'bitbucket.org',
            '--detach',
        ]
        for volume in volumes:
            if isinstance(volume, dict):
                volume_ = volume['name']
                if volume.get('temp', False):
                    if volume_.startswith('/'):
                        raise Exception('Unsupported temp volume type')
                    volume_ = 'AUTODELETE_' + volume_
            else:
                volume_ = volume
            volume_ = volume_ % {'buildnumber': buildnumber}
            cmd.append('--volume=%s' % volume_)

        cmd.append(image)
        self.instance = self.docker_invoke(*cmd)
        self.logger.debug('Container created, Id: %s...' % self.instance)
        return [self.instance, image]

    def _thd_stop_instance(self, instance, fast):
        self.logger.debug('Stopping container %s...' % instance)
        mounts = loads(self.docker_invoke(
            "inspect",
            "--format='{{ json .Mounts }}'",
            instance)) or {}
        self.docker_invoke('kill', instance)
        self.docker_invoke('wait', instance)
        self.docker_invoke('rm', instance)
        for mount in mounts:
            mount_name = mount.get('Name', '')
            if mount_name.startswith('AUTODELETE_'):
                self.docker_invoke('volume', 'rm', mount_name)
        self.logger.debug('Container %s stopped successfully.' % instance)

    def docker_invoke(self, *args):
        """calls the docker client binary with the arguments given as a
         parameter and logs exceptions if any.
         Returns the output of the commmand (stderr + stdout)

         """
        cmd = ['docker']
        if self.docker_tls_verify == '1':
            cmd.extend([
                '--tlsverify',
                '--tlscacert=%s/ca.pem' % self.docker_cert_path,
                '--tlscert=%s/cert.pem' % self.docker_cert_path,
                '--tlskey=%s/key.pem' % self.docker_cert_path,
                '--host=%s' % self.docker_host,
            ])
        cmd.extend(args)
        try:
            res = check_output(cmd, stderr=STDOUT).strip()
            return res
        except CalledProcessError as exception:
            time.sleep(5)  # avoid a fast loop in case of failure
            self.logger.debug('Error: command %s failed: %s' %
                              (cmd, exception.output))
            raise
