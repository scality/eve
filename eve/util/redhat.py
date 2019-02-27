# Copyright 2019 Scality
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

from buildbot.process import remotecommand
from twisted.internet import defer


@defer.inlineCallbacks
def isRedhat(step):
    """Return true if the worker's OS is RedHat.

    Used as a step parameter (per example 'doStepIf') to identify wheiter
    the worker is using Redhat as a OS or another.

    """

    command = "rpm -qa | grep -qE '^redhat-release.+'"
    cmd = remotecommand.RemoteShellCommand('/', command)
    yield step.runCommand(cmd)
    defer.returnValue(not cmd.didFail())
