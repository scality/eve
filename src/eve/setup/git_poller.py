from buildbot.changes.gitpoller import GitPoller
from buildbot.plugins import util


def git_poller():
    if not util.env.GIT_POLLING:
        return []

    return GitPoller(
        util.env.GIT_REPO,
        workdir='gitpoller-workdir',
        branches=True,
        pollinterval=900,
        pollAtLaunch=False,
        buildPushesWithNoCommits=True,
    )
