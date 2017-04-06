from buildbot.plugins import util
from buildbot.process.properties import Interpolate
from buildbot.process.results import CANCELLED, SUCCESS
from buildbot.steps.master import MasterShellCommand


class CancelCommand(MasterShellCommand):
    """Cancel a build according to result of command."""

    def processEnded(self, status_object):
        """If the return code is non-zero set build to CANCELLED."""
        if status_object.value.exitCode != 0:
            self.finished(CANCELLED)
        else:
            super(CancelCommand, self).processEnded(status_object)


class CancelNonTipBuild(CancelCommand):
    """Cancel if the current revision is not the tip of the branch."""

    def __init__(self, **kwargs):
        super(CancelNonTipBuild, self).__init__(
            name='check if build is relevant',
            command=Interpolate('[ "%(prop:revision)s" = "" ]'
                                '|| [ "$(git rev-list -1 %(prop:branch)s)"'
                                ' = "%(prop:revision)s" ]'),
            hideStepIf=lambda results, s: results == SUCCESS,
            **kwargs
        )


class CancelOldBuild(CancelCommand):
    """Cancel if the build is previous buildbot instance."""

    def __init__(self, **kwargs):
        # pylint: disable=anomalous-backslash-in-string
        super(CancelOldBuild, self).__init__(
            name='prevent unuseful restarts',
            hideStepIf=lambda results, s: results == SUCCESS,
            command=Interpolate('[ $(expr "' + util.env.MASTER_START_TIME +
                                '" \< "%(prop:start_time)s") -eq 1 ]'),
        )
