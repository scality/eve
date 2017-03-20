from os import environ, path

from buildbot.plugins import worker
from buildbot.process.properties import Property

from ..utils.password_generator import password_generator


def setup_openstack_workers(max_openstack_workers, worker_suffix, master_fqdn,
                            credentials):

    openstack_identity_url = 'https://identity.api.rackspacecloud.com/v2.0/'
    openstack_region = environ.get('OPENSTACK_REGION', 'DFW')
    openstack_tenant = 984990
    openstack_ssh_key = path.expanduser(
        environ.get('OPENSTACK_SSH_KEY', '~/.ssh/id_rsa'))
    openstack_key_name = environ.get('OPENSTACK_KEY_NAME', 'eve-key-pair')
    cloud_init_script = environ.pop('CLOUD_INIT_SCRIPT', None)

    openstack_workers = []
    for i in range(max_openstack_workers):
        openstack_workers.append(
            worker.EveOpenStackLatentWorker(
                name='ow%03d-%s' % (i, worker_suffix),
                password=password_generator(),
                image=Property('openstack_image'),
                flavor=Property('openstack_flavor'),
                block_devices=None,
                os_auth_url=openstack_identity_url,
                os_tenant_name=openstack_tenant,
                os_username=credentials['login'],
                os_password=credentials['password'],
                region=openstack_region,
                cloud_init=cloud_init_script,
                ssh_key=openstack_ssh_key,
                meta=None,
                masterFQDN=master_fqdn,
                nova_args=dict(key_name=openstack_key_name),
                build_wait_timeout=0,  # do not reuse the instance
                keepalive_interval=300,
                client_version='2'))
    return openstack_workers
