from buildbot.plugins import util, worker
from buildbot.process.properties import Property
from buildbot.worker.local import LocalWorker
from twisted.python.reflect import namedModule


def local_workers():
    workers = []
    for i in range(util.env.MAX_LOCAL_WORKERS):
        worker_ = LocalWorker('lw%03d-%s' % (i, util.env.SUFFIX))
        # Hack to fix a bug stating that LocalWorkers
        # do not have a valid path_module
        worker_.path_module = namedModule('posixpath')
        workers.append(worker_)
    return workers


def docker_workers():
    workers = []
    for i in range(util.env.MAX_DOCKER_WORKERS):
        workers.append(
            worker.EveDockerLatentWorker(
                name='dw%03d-%s' % (i, util.env.SUFFIX),
                password=util.password_generator(),
                master_fqdn=util.env.MASTER_FQDN,
                pb_port=util.env.PB_PORT,
                artifacts_prefix=util.env.ARTIFACTS_PREFIX,
                max_memory=util.env.DOCKER_CONTAINER_MAX_MEMORY,
                max_cpus=util.env.DOCKER_CONTAINER_MAX_CPU,
                image=Property('docker_image'),
                keepalive_interval=300,
            ))
    return workers


def openstack_workers():
    workers = []
    for i in range(util.env.MAX_OPENSTACK_WORKERS):
        workers.append(
            worker.EveOpenStackLatentWorker(
                name='ow%03d-%s' % (i, util.env.SUFFIX),
                password=util.password_generator(),
                image=Property('openstack_image'),
                flavor=Property('openstack_flavor'),
                block_devices=None,
                os_auth_url=util.env.OS_AUTH_URL,
                os_tenant_name=util.env.OS_TENANT,
                os_username=util.env.RAX_LOGIN,
                os_password=util.env.RAX_PWD,
                region=util.env.OS_REGION,
                ssh_key=util.env.OS_SSH_KEY,
                cloud_init=util.env.CLOUD_INIT_SCRIPT,
                meta=None,
                masterFQDN=util.env.MASTER_FQDN,
                pb_port=util.env.PB_PORT,
                nova_args=dict(key_name=util.env.OS_KEY_NAME),
                build_wait_timeout=0,  # do not reuse the instance
                keepalive_interval=300,
                client_version='2'))
    return workers
