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

from buildbot.steps.shell import ShellCommand


class UnregisterRedhat(ShellCommand):
    """Executed on redhat workers to unregister from the customer portal."""

    name = 'UnregisterRedhat'
    description = ['Unregister this system from Red Hat Customer Portal']
    descriptionDone = ['Unregistered from Red Hat Customer Portal']
    alwaysRun = True
    flunkOnFailure = False
    command = 'sudo subscription-manager unregister'
