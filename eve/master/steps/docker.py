"""All docker related steps."""

from buildbot.locks import MasterLock
from buildbot.steps.master import MasterShellCommand
from buildbot.process.results import FAILURE
from twisted.internet import defer

DOCKER_BUILD_LOCK = MasterLock("docker_build")


class DockerBuild(MasterShellCommand):
    """Step to build a docker image on eve docker host."""

    def __init__(self, image, dockerfile=None, is_retry=False, **kwargs):
        self.image = image
        self.is_retry = is_retry
        kwargs.setdefault('locks', []).append(
            DOCKER_BUILD_LOCK.access('exclusive'))

        command = [
            "docker", "build",
            "-t", image
        ]

        if dockerfile is not None:
            command += ["-f", dockerfile]

        if is_retry:
            command += ["--no-cache"]

        command += ["."]

        super(DockerBuild, self).__init__(command, **kwargs)

    def isNewStyle(self): # flake8: noqa
        # needed because we redefine `run` below
        return False

    @defer.inlineCallbacks
    def run(self):
        result = yield super(DockerBuild, self).run()
        if result == FAILURE:
            properties = self.build.getProperties()
            properties.setProperty(
                'DockerBuildFailed', self.image, self.name, runtime=True)
        defer.returnValue(result)

    def __hash__(self):
        return hash(self.image)

    def __eq__(self, other):
        return (isinstance(other, DockerBuild) and
                self.image == other.image and
                (self.is_retry) == (other.is_retry))
