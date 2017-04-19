"""HACK to not restart a worker substantiating on failure."""
import buildbot.process.build
from buildbot.process.results import FAILURE


def patch():
    buildbot.process.build.RETRY = FAILURE
