"""All docker related steps."""

from buildbot.locks import MasterLock
from buildbot.steps.master import MasterShellCommand


DOCKER_BUILD_LOCK = MasterLock("docker_build")


class DockerBuild(MasterShellCommand):
    """Step to build a docker image on eve docker host."""

    def __init__(self, image, dockerfile=None, **kwargs):
        self.image = image
        kwargs.setdefault('locks', []).append(
            DOCKER_BUILD_LOCK.access('exclusive'))

        command = [
            "docker", "build",
            "-t", image
        ]

        if dockerfile is not None:
            command += ["-f", dockerfile]

        command += ["."]

        super(DockerBuild, self).__init__(command, **kwargs)

    def __hash__(self):
        return hash(self.image)

    def __eq__(self, other):
        return self.image == other.image
