import subprocess

from buildbot.schedulers.forcesched import ForceScheduler, ValidationError
from twisted.internet import defer, threads


class EveForceScheduler(ForceScheduler):

    @defer.inlineCallbacks
    def gatherPropertiesAndChanges(self, collector, **kwargs):
        properties, changeids, sourcestamps = \
            yield super(EveForceScheduler, self).gatherPropertiesAndChanges(
                collector, **kwargs
            )

        yield collector.collectValidationErrors('branch',
                                                self.add_missing_revisions,
                                                sourcestamps)

        defer.returnValue((properties, changeids, sourcestamps))

    @staticmethod
    @defer.inlineCallbacks
    def add_missing_revisions(sourcestamps):
        for _, sourcestamp in sourcestamps.iteritems():
            if not sourcestamp['revision']:
                # Retrieve revision from branch for sourcestamps without one
                res = yield threads.deferToThread(
                    subprocess.check_output,
                    ['git', 'ls-remote', sourcestamp['repository'],
                     sourcestamp['branch']],
                    stderr=subprocess.PIPE,
                )
                try:
                    sourcestamp['revision'] = res.split()[0]
                except IndexError:
                    raise ValidationError("'%s' branch not found" %
                                          sourcestamp['branch'])
