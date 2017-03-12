from buildbot.changes.gitpoller import GitPoller

EVE_GIT_POLLING = False


def setup_git_poller(conf, git_repo):
    conf['change_source'] = []
    if EVE_GIT_POLLING:
        conf['change_source'].append(GitPoller(
            git_repo,
            workdir='gitpoller-workdir',
            branches=True,
            pollinterval=900,
            pollAtLaunch=False,
            buildPushesWithNoCommits=True,
        ))
