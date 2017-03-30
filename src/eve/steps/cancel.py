from buildbot.plugins import util
from buildbot.process.properties import Interpolate
from buildbot.process.results import CANCELLED, SUCCESS
from buildbot.steps.shell import ShellCommand


class CancelCommand(ShellCommand):
    """Cancel a build according to result of command."""

    def commandComplete(self, cmd):
        if cmd.didFail():
            self.finished(CANCELLED)
            return

        return super(CancelCommand, self).commandComplete(cmd)


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
