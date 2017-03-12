from buildbot.process.properties import Property

from utils.password_generator import password_generator
from workers.docker.docker_worker import EveDockerLatentWorker


def setup_docker_workers(max_docker_workers, worker_suffix, master_fqdn):
    docker_workers = []
    for i in range(max_docker_workers):
        docker_workers.append(
            EveDockerLatentWorker(
                name='dw%03d-%s' % (i, worker_suffix),
                password=password_generator(),
                master_fqdn=master_fqdn,
                image=Property('docker_image'),
                keepalive_interval=300,
            ))
    return docker_workers
