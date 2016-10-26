"""Allow eve to use docker workers."""

from os import environ
from subprocess import STDOUT, CalledProcessError, check_output
import time

from buildbot.worker.docker import DockerLatentWorker
import netifaces
from twisted.logger import Logger


class EveDockerLatentWorker(DockerLatentWorker):
    """Improved version of DockerLatentWorker using the docker command line
     client instead of docker-py which was the cause of multiple dead locks
    """
    logger = Logger('eve.workers.EveDockerLatentWorker')

    def _thd_start_instance(self, image, volumes):
        if image not in self.docker_invoke('images'):
            # hack to avoid a loop when the original image does not exist
            self.docker_invoke('pull', 'ubuntu:trusty')
            image = 'ubuntu:trusty'

        docker_host_ip = None
        try:
            docker_host_ip = netifaces.ifaddresses('docker0')[2][0]['addr']
        except Exception:  # FIXME: do we need such a generic exception?
            pass

        cmd = [
            'run',
            '--privileged',
            '--env', 'BUILDMASTER=%s' % self.masterFQDN,
            '--env', 'WORKERNAME=%s' % self.name,
            '--env', 'WORKERPASS=%s' % self.password,
            '--env', 'BUILDMASTER_PORT=%s' % environ['PB_PORT'],
            '--env', 'DOCKER_HOST_IP=%s' % docker_host_ip,
            '--env', 'ARTIFACTS_PREFIX=%' % environ['ARTIFACTS_PREFIX'],
            '--link', 'bitbucket.org',
            '--detach',
        ]
        cmd.extend(['--volume=%s' % volume for volume in volumes])
        cmd.append(image)
        self.instance = self.docker_invoke(*cmd)
        self.logger.debug('Container created, Id: %s...' % self.instance)
        return [self.instance, image]

    def _thd_stop_instance(self, instance, fast):
        self.logger.debug('Stopping container %s...' % instance)
        self.docker_invoke('kill', instance)
        self.docker_invoke('wait', instance)
        self.docker_invoke('rm', instance)
        self.logger.debug('Container %s stopped successfully.' % instance)

    def docker_invoke(self, *args):
        """calls the docker client binary with the arguments given as a
         parameter and logs exceptions if any.
         Returns the output of the commmand (stderr + stdout)

         """
        cmd = ['docker']
        cmd.extend(args)
        try:
            res = check_output(cmd, stderr=STDOUT).strip()
            return res
        except CalledProcessError as exception:
            time.sleep(5)  # avoid a fast loop in case of failure
            self.logger.debug('Error: command %s failed: %s' %
                              (cmd, exception.output))
            raise
