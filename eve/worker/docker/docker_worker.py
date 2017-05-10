# Copyright 2017 Scality
#
# This file is part of Eve.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
"""Allow eve to use docker workers."""

import time
from json import loads
from subprocess import STDOUT, CalledProcessError, check_output

import netifaces
from buildbot.plugins import util
from buildbot.process.properties import Property
from buildbot.worker.latent import AbstractLatentWorker
from twisted.internet import defer, threads
from twisted.logger import Logger
from twisted.python import log


class EveDockerLatentWorker(AbstractLatentWorker):
    """Eve version on the DockerLetentWorker.

    Improved version of DockerLatentWorker using the docker command line client
    instead of docker-py which was the cause of multiple dead locks.

    """

    logger = Logger('eve.workers.EveDockerLatentWorker')
    instance = None

    def __init__(self, name, password, image, master_fqdn, pb_port,
                 artifacts_prefix, max_memory, max_cpus, **kwargs):
        # pylint: disable=too-many-arguments
        self.image = image
        self.master_fqdn = master_fqdn,
        self.pb_port = pb_port
        self.artifacts_prefix = artifacts_prefix
        self.max_memory = max_memory
        self.max_cpus = max_cpus
        kwargs.setdefault('build_wait_timeout', 0)
        kwargs.setdefault('keepalive_interval', None)
        AbstractLatentWorker.__init__(self, name, password, **kwargs)

    @defer.inlineCallbacks
    def start_instance(self, build):
        if self.instance is not None:
            raise ValueError('instance active')
        image = yield build.render(self.image)
        volumes = build.getProperty('docker_volumes')
        buildnumber = yield build.render(Property('buildnumber'))
        res = yield threads.deferToThread(self._thd_start, image,
                                          volumes, buildnumber)
        defer.returnValue(res)

    def _thd_start(self, image, volumes, buildnumber):
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
            '--env', 'BUILDMASTER=%s' % self.master_fqdn,
            '--env', 'WORKERNAME=%s' % self.name,
            '--env', 'WORKERPASS=%s' % self.password,
            '--env', 'BUILDMASTER_PORT=%s' % self.pb_port,
            '--env', 'DOCKER_HOST_IP=%s' % docker_host_ip,
            '--env', 'ARTIFACTS_PREFIX=%s' % self.artifacts_prefix,
            '--detach',
            '--memory=%s' % self.max_memory,
            '--cpus=%s' % self.max_cpus
        ]

        if util.env.GITCACHE_IN_USE:
            hostname = util.env.GITCACHE_HOSTNAME
            port = util.env.GITCACHE_PORT
            cmd += [
                '--env', 'GITCACHE_HOSTNAME=%s' % hostname,
                '--env', 'GITCACHE_PORT=%s' % port,
                '--link', hostname]

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

    def stop_instance(self, fast=False):
        assert not fast  # unused parameter, we cannot remove it (PEP8)
        if self.instance is None:
            return defer.succeed(None)
        instance = self.instance
        self.instance = None
        return threads.deferToThread(self._thd_stop_instance, instance)

    def _thd_stop_instance(self, instance):
        self.logger.debug('Stopping container %s...' % instance)

        mounts_content = self.docker_invoke(
            'inspect',
            '--format', '{{ json .Mounts }}',
            instance
        )

        try:
            mounts = loads(mounts_content)
        except (TypeError, ValueError) as exc:
            log.msg('Output: %r' % mounts_content)
            log.err(exc, 'Error: Unable to parse JSON content'
                         ' from docker inspect command')
            mounts = None

        self.docker_invoke('kill', instance)
        self.docker_invoke('wait', instance)
        self.docker_invoke('rm', '--volumes', instance)
        if mounts:
            for mount in mounts:
                mount_name = mount.get('Name', '')
                if mount_name.startswith('AUTODELETE_'):
                    self.docker_invoke('volume', 'rm', mount_name)
        self.logger.debug('Container %s stopped successfully.' % instance)

    def docker_invoke(self, *args):
        """Call the docker client binary.

        It calls the `docker` command with the arguments given as a parameter
        and logs exceptions if any.

        Args:
            *args: Arguments to pass to `docker`.

        Returns:
            str: The output of the commmand (stderr + stdout).

        """
        cmd = ['docker']
        cmd.extend(args)
        cmd_shell = ' '.join(cmd)
        try:
            self.logger.debug('::RUNNING::{}'.format(cmd_shell))
            res = check_output(cmd, stderr=STDOUT).strip()
            return res
        except CalledProcessError as exception:
            time.sleep(5)  # avoid a fast loop in case of failure
            raise RuntimeError('CalledProcessError: {} *** OUTPUT: {}'.format(
                cmd_shell,
                exception.output
            ))
