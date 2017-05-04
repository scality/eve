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

from buildbot.plugins import util
from buildbot.steps.shell import ShellCommand


class ShellCommandWithSecrets(ShellCommand):
    """Execute a shell command that needs secret environment variables.

    All variables on the form SECRET_{var} will be passed as {var} inside the
    worker. Naturally, the environment is not logged during such a step.

    """

    def __init__(self, *args, **kwargs):
        new_env = kwargs.pop('env', {})
        new_env.update(util.get_secrets())

        kwargs.update({
            'logEnviron': False,
            'env': new_env,
        })

        super(ShellCommandWithSecrets, self).__init__(*args, **kwargs)
