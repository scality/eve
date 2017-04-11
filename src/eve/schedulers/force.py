import subprocess

from buildbot.schedulers.forcesched import ForceScheduler
from twisted.internet import defer, threads


class EveForceScheduler(ForceScheduler):

    @defer.inlineCallbacks
    def gatherPropertiesAndChanges(self, collector, **kwargs):
        properties, changeids, sourcestamps = \
            yield super(EveForceScheduler, self).gatherPropertiesAndChanges(
                collector, **kwargs
            )

        yield threads.deferToThread(self.add_missing_revisions, sourcestamps)

        defer.returnValue((properties, changeids, sourcestamps))

    @staticmethod
    def add_missing_revisions(sourcestamps):
        for _, sourcestamp in sourcestamps.iteritems():
            if not sourcestamp['revision']:
                try:
                    # Retrieve revision from branch for sourcestamps without one
                    sourcestamp['revision'] = subprocess.check_output(
                        ['git', 'ls-remote', sourcestamp['repository'],
                         sourcestamp['branch']],
                        stderr=subprocess.PIPE,
                    ).split()[0]
                except IndexError:
                    sourcestamp['revision'] = None
