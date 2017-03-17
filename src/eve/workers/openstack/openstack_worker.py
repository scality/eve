"""Allow eve to use openstack workers."""

import re
import time
from os import environ
from subprocess import STDOUT, CalledProcessError, check_output

import novaclient
from buildbot.process.properties import Property
from buildbot.worker import AbstractWorker
from buildbot.worker.openstack import OpenStackLatentWorker
from retrying import retry
from twisted.internet import defer, threads
from twisted.logger import Logger
from twisted.python import log

from ..ngrok import Ngrok


class EveOpenStackLatentWorker(OpenStackLatentWorker):
    """Improved version of OpenStackLatentWorker that adds:
    - Support for regions (Required for Rackspace)
    - Automatically installs a buildbot worker after spawn using ssh
    """
    logger = Logger('eve.EveOpenStackLatentWorker')

    # (address, port) tuple used to configure buildbot-worker on VM
    _reachable_address = None

    # Ngrok instance, if used (if env var NGROK is set)
    _ngrok = None

    def get_reachable_address(self):
        """Get the address to the eve master reachable by the worker."""
        if not self._reachable_address:
            if 'NGROK' in environ:
                self._ngrok = Ngrok(command=environ['NGROK'])
                self._reachable_address = self._ngrok.start(
                    'tcp', environ['PB_PORT'], 'us')
            else:
                self._reachable_address = self.masterFQDN, environ['PB_PORT']
        return self._reachable_address

    def __init__(self, region, ssh_key, masterFQDN,
                 cloud_init=None, **kwargs):  # flake8: noqa
        super(EveOpenStackLatentWorker, self).__init__(**kwargs)
        # fixme: This is a fragile hack because the original class does not
        # allow to specify a region name. We should fix this upstream.
        self.novaclient.client.region_name = region
        self.ssh_key = ssh_key
        self.cloud_init = cloud_init
        self.ip_address = None
        self.masterFQDN = masterFQDN
        self._ngrok = None
        self._starting_instance = False

    def ssh(self, cmd):
        """ Execute an ssh command on the instance.
        :param cmd: The command to launch
        :return: the output of the command
        """
        self.logger.debug('Executing "%s" on %s %s' %
                          (cmd, self.workername, self.ip_address))
        res = check_output(
            'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no '
            '-o SendEnv=LC_ALL -i %s root@%s \'%s\'' % (
                self.ssh_key, self.ip_address, cmd),
            shell=True, stderr=STDOUT)
        return res

    def scp(self, src, dst):
        """
        Send files to instance using scp
        :param src: the source file
        :param dst: the destination file
        :return:
        """
        self.logger.debug('Copying %s to on %s %s:%s ' %
                          (src, self.ip_address, dst, self.workername))
        res = check_output(
            'scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no '
            '-o SendEnv=LC_ALL -i %s %s root@%s:%s' % (
                self.ssh_key, src, self.ip_address, dst),
            shell=True, stderr=STDOUT)
        return res

    def ssh_ping(self):
        """Dummy command to test ssh connexion."""
        self.ssh('ls')

    @defer.inlineCallbacks
    def start_instance(self, build):
        """Replace buildbot start_instance for OpenStackLatentWorker.

        This new method is inspired by DockerLatentWorker, and allows
        to use Properties for `image` and `flavor`; This in turns allows
        to configure the type of OpenStack machine from the project
        YAML.

        Fragile fix, and should be fixed upstream preferably.

        """
        if self.instance is not None:
            raise ValueError('instance active')
        image = yield build.render(Property('openstack_image'))
        flavor = yield build.render(Property('openstack_flavor'))
        master_builddir = yield build.render(Property('master_builddir'))
        worker_path = yield build.render(Property('worker_path'))
        init_script = "%s/build/%s/init.sh" % (master_builddir, worker_path)

        self._starting_instance = True
        try:
            res = yield threads.deferToThread(self._start, image,
                                              flavor, init_script)
            defer.returnValue(res)
        finally:
            self._starting_instance = False

    @retry(wait_exponential_multiplier=10000, stop_max_delay=300000)
    # 10s exponential backoff and giving up after about five minutes
    def _start(self, image, flavor, init_script):
        self.logger.debug('Spawning Openstack machine'
                          ' <image:{}> <flavor:{}> <init_script:{}>...'.
                          format(image, flavor, init_script))

        # delete any existing instance of this worker (from previous trials)
        servers = get_active_servers_by_name(self.workername, self.novaclient)
        for instance in servers:
            self._stop_instance(instance, False)

        image_obj = get_openstack_image_by_name(image, self.novaclient)
        self.logger.debug('Openstack image UUID: {}'.format(image_obj.id))
        self.flavor = flavor
        result = super(EveOpenStackLatentWorker, self)._start_instance(
            image_obj, None)
        if not self.instance:
            return result

        inst = self.novaclient.servers.get(self.instance.id)
        for network in inst.networks[u'public']:
            if re.match(r'\d+\.\d+\.\d+\.\d+', network):
                self.ip_address = network
                break
        else:
            assert False, 'Could not extract IP address'

        for _ in range(30):
            time.sleep(2)
            try:
                self.ssh_ping()
                break
            except CalledProcessError as exception:
                self.logger.debug('Pinging host %s %s <%s> %s. Retrying...' % (
                    self.workername, self.ip_address,
                    exception, exception.output))

        try:
            self.start_worker(init_script)
        except CalledProcessError as exception:
            self.logger.debug('Error on %s %s while executing "%s" <%s> %s.' %
                              (self.workername, self.ip_address,
                               exception.cmd, exception, exception.output))
            raise
        return result

    def start_worker(self, init_script):
        """Execute init scripts remotely and launches buildbot worker.

        - run the init script provided by project (installs buildbot,
          creates user `eve` for target system)
        - run cloud init script, common to all workers (typically: adds
          ssh keys)
        - instanciate buildbot worker

        """
        self.scp(init_script, '/tmp/worker_init.sh')
        self.ssh(' && '.join([
            'chmod u+x /tmp/worker_init.sh',
            '/tmp/worker_init.sh 0.9.3'
        ]))

        if self.cloud_init:
            self.scp(self.cloud_init, '/tmp/cloud_init.sh')
            self.ssh(' && '.join([
                'chmod u+x /tmp/cloud_init.sh',
                '/tmp/cloud_init.sh'
            ]))

        master, port = self.get_reachable_address()
        self.ssh('sudo -u eve buildbot-worker create-worker --umask=022 '
                 '/home/eve/worker %s:%s %s "%s"' %
                 (master, port, self.name, self.password))

        self.ssh('sudo -u eve buildbot-worker start /home/eve/worker')

    def buildFinished(self, sb):  # NOQA flake8 to ignore camelCase
        super(EveOpenStackLatentWorker, self).buildFinished(sb)

        # This is a hack to avoid the bug of vms staying in 'preparing worker'
        # for hours
        # what happens is : we setup the openstack VM in start_worker called in
        # start_instance, which is called by substantiate, only if self.conn
        # is None (seems to be intended to be called one time only per worker,
        # whereas our start_instance is written to run 1 time per VM)
        if self.conn:
            self.conn.detached(None)

    def stop_instance(self, fast=False):

        if self.instance is None:
            # be gentle.  Something may just be trying to alert us that an
            # instance never attached, and it's because, somehow, we never
            # started.
            return defer.succeed(None)
        instance = self.instance
        self.instance = None

        # this allows to call the vm deletion in a thread so we can wait
        # until we are sure they are deleted (Not the case in the original
        # class)
        threads.deferToThread(self._stop_instance, instance, fast)

        return AbstractWorker.disconnect(self)

    def _stop_instance(self, instance, fast):
        try:
            inst = self.novaclient.servers.get(instance.id)
        except novaclient.exceptions.NotFound:
            # If can't find the instance, then it's already gone.
            self.logger.info(
                '%s %s instance %s (%s) does not exist' %
                (self.__class__.__name__, self.workername, instance.id,
                 instance.name))
            return

        if inst.status in ('DELETED', 'UNKNOWN'):
            self.logger.info(
                '%s %s instance %s (%s) already deleted' %
                (self.__class__.__name__, self.workername, instance.id,
                 instance.name))
            return

        inst.delete()
        while inst.status == 'ACTIVE':
            try:
                time.sleep(10)
                inst.get()
                self.logger.info(
                    '%s %s instance %s (%s) waiting for deletion' %
                    (self.__class__.__name__, self.workername, instance.id,
                     instance.name))
            except novaclient.exceptions.NotFound:
                break

        self.logger.info(
            '%s %s instance %s (%s) deleted successfully' %
            (self.__class__.__name__, self.workername,
             instance.id, instance.name))

    def detached(self):
        AbstractWorker.detached(self)
        if self._starting_instance:
            # Hack to avoid a race condition.
            # If we are currently spawning an openstack worker, then this
            # method is called because an older instance has just disconnected.
            #
            # In such a case, since we're in the middle of a substanciation,
            # OpenstackLatentWokrer.detached() would believe that we were
            # waiting for the former worker to detach before substanciating a
            # new one, and would attempt to call start_instance(), which can
            # only result in an exception being triggered.
            #
            # Bottomline: it is safe to simply ignore the 'detach' event here.
            return
        if self._substantiation_notifier:
            deferred = self._substantiate(self.substantiation_build)
            deferred.addErrback(log.err, 'while re-substantiating')


def get_active_servers_by_name(server_name, nova_client):
    """Get all active servers having a given name.

        :param server_name: the server name we are looking for
        :param nova_client: a nova client

        :return: a list of servers having given name.
    """
    return nova_client.servers.list(search_opts={'name': server_name})


def get_openstack_image_by_name(image_name, nova_client):
    """Identification of an OpenStack image based on its name.

        :param image_name: a list of nova image objects
        :param nova_client: a nova client
        :return: the image that matches the name
        """

    images = nova_client.images.list()
    for image in images:
        if image.name == image_name:
            return image

    raise RuntimeError('Error: Openstack image <%s> not found on the '
                       'openstack server image list : <%s>' % (
                           image_name, [
                               image.name for image in images]
                       ))
