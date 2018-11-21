# Copyright 2017 Scality
#
# This file is part of Eve.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.

from functools import wraps

from buildbot.plugins import util
from buildbot.process.remotecommand import RemoteShellCommand


def update_timeouts(func):
    """Enforce RemoteShellCommand maxTime and timeout arguments.

    Eve supports specifying timeout values as properties (e.g.
    prop:step_maxtime).

    When specified as a property, i.e. an interpolatable, the timeout
    will be rendered into an int-string (e.g. '5'). Buildbot workers
    only accepts pure ints.

    This wrapper:
    - sets a default maxtime if none is specified,
    - ensures we pass an int to the worker,
    - fails if given maxtime is not an int or int-string,
    - fails if given maxtime is larger than max allowed value,
    - fails if timeout is larger than max allowed value,

    Note: the complete list of arguments is specified in the wrapper
          because the original RemoteShellCommand.__init__ does
          argument introspection, so this patch is not allowed to
          change the signature of the method.

    """
    @wraps(func)
    def wrapper(self, workdir, command, env=None,
                want_stdout=1, want_stderr=1,
                timeout=20 * 60, maxTime=None, sigtermTime=None,
                logfiles=None, usePTY=None, logEnviron=True,
                collectStdout=False, collectStderr=False,
                interruptSignal=None,
                initialStdin=None, decodeRC=None,
                stdioLogName='stdio'):

        if not maxTime:
            maxTime = util.env.MAX_STEP_DURATION

        maxTime = int(maxTime)

        if maxTime > util.env.MAX_STEP_DURATION:
            raise ValueError('specified maxTime is larger than '
                             'authorized maximum on this project (%ss > %ss)' %
                             (maxTime, util.env.MAX_STEP_DURATION))
        if timeout is not None:
            timeout = int(timeout)

            if timeout > util.env.MAX_STEP_DURATION:
                raise ValueError('specified timeout is larger than '
                                'authorized maximum on this project (%ss > %ss)' %
                                (timeout, util.env.MAX_STEP_DURATION))

        return func(
            self, workdir, command, env=env,
            want_stdout=want_stdout, want_stderr=want_stderr,
            timeout=timeout, maxTime=maxTime, sigtermTime=sigtermTime,
            logfiles=logfiles, usePTY=usePTY, logEnviron=logEnviron,
            collectStdout=collectStdout, collectStderr=collectStderr,
            interruptSignal=interruptSignal,
            initialStdin=initialStdin, decodeRC=decodeRC,
            stdioLogName=stdioLogName)

    return wrapper


def patch():
    RemoteShellCommand.__init__ = update_timeouts(RemoteShellCommand.__init__)
