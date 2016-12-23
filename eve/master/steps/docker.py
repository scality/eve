"""All docker related steps."""

from buildbot.locks import MasterLock
from buildbot.steps.master import MasterShellCommand


DOCKER_BUILD_LOCK = MasterLock("docker_build")


class DockerBuild(MasterShellCommand):
    """Step to build a docker image on eve docker host."""

    def __init__(self, image, **kwargs):
        self.image = image
        if self.DOCKER_TLS_VERIFY == '1':
            docker_cmd = [
                'docker',
                '--tlsverify',
                '--host=%s' % self.DOCKER_HOST,
                '--tlscacert=%s' % self.DOCKER_CERT_PATH_CA,
                '--tlscert=%s ' % self.DOCKER_CERT_PATH_CERT,
                '--tlskey=%s' % self.DOCKER_CERT_PATH_KEY,
                'build',
            ]
        else:
            docker_cmd = ['docker', 'build']

        kwargs.setdefault('locks', []).append(
            DOCKER_BUILD_LOCK.access('exclusive'))

        super(DockerBuild, self).__init__(
            command='%s -t %s .' % (' '.join(docker_cmd), image),
            **kwargs
        )

    def __hash__(self):
        return hash(self.image)

    def __eq__(self, other):
        return self.image == other.image
