import buildbot.process.build
from buildbot.process import buildrequest
from buildbot.process.buildstep import BuildStep
from buildbot.process.results import FAILURE
from twisted.python.reflect import namedModule

from ..bugfixes.tempsourcestamp import TempSourceStamp
from ..utils.interpolate import (hide_interpolatable_name,
                                 render_interpolatable_name)


def setup_hacks(conf):
    # Hack to allow build step name interpolation
    BuildStep.__init__ = hide_interpolatable_name(BuildStep.__init__)
    BuildStep.startStep = render_interpolatable_name(BuildStep.startStep)

    # Hack to fix a bug stating that LocalWorkers do not have a valid
    # path_module
    for worker in conf['workers']:
        worker.path_module = namedModule('posixpath')

    # Compressed logs generate a lot of issues like this :
    # 2016-08-28 14:17:22+0000 [-] /root/eve/workspaces/ring/venv/local/lib/
    # python2.7/site-packages/sqlalchemy/engine/default.py:451:
    # _mysql_exceptions.Warning: Invalid utf8 character string: 'DAC554'
    # This hack fixes them by disabling log compression
    conf['logCompressionMethod'] = 'raw'

    # Hack to fix a bug where the git diff is sent as an str instead of
    # unicode and triggers an exception
    buildrequest.TempSourceStamp = TempSourceStamp

    # Hack to not restart a worker substantiating on failure
    buildbot.process.build.RETRY = FAILURE
