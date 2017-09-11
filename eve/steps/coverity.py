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
"""Step allowing eve to run coverity test."""

import os

from buildbot.plugins import steps, util
from buildbot.process import logobserver


class CoverityCommand(steps.ShellSequence):
    """Run coverity test."""

    def __init__(self, command, **kwargs):
        kwargs.pop('name', 'Run coverity test')

        super(CoverityCommand, self).__init__(
            commands=util.Transform(self.set_commands, command),
            **kwargs
        )
        self.name = 'Run coverity test'
        self.observer = logobserver.BufferLogObserver(wantStdout=True,
                                                      wantStderr=True)
        self.addLogObserver('stdio', self.observer)

    def set_commands(self, command):
        repo_dir = '/home/eve/workspace/docker-backend/build/'
        build_dir = '/home/eve/workspace/build_dir'
        coverity_server = "51.254.50.74"
        data_port = "9090"
        username = "admin"
        user_pwd = "Scality_2016"
        langage = "cpp"
        scm = "git"

        commands = [
            util.ShellArg(
                command=str('cov-manage-im --mode projects --add --set name:"'
                            + self.getProperty('project').replace('/', '_')
                            + '" --host ' + coverity_server + ' --user '
                            + username + ' --password ' +
                            user_pwd), flunkOnFailure=False, logfile='stdio'),

            util.ShellArg(
                command=str('mkdir -p ' + os.path.join(
                    build_dir, self.getProperty('project').replace('/', '_'),
                    self.getProperty('branch').replace('/', '_')
                    .replace('-', '_'))),
                haltOnFailure=True, logfile='stdio'),

            util.ShellArg(
                command=str('cov-manage-im --mode streams --add --set name:"' +
                            (self.getProperty('project') +
                             '_' + self.getProperty('branch'))
                            .replace('/', '_').replace('-', '_') +
                            '" --set lang:"' + langage +
                            '" --set triage:"Default Triage Store" --host ' +
                            coverity_server + ' --user ' + username +
                            ' --password ' + user_pwd), flunkOnFailure=False,
                logfile='stdio'),

            util.ShellArg(
                command=str(
                    'cov-manage-im --mode projects --update --name ' +
                    self.getProperty('project').replace('/', '_') +
                    ' --insert stream:"' +
                    (self.getProperty('project') + '_' +
                     self.getProperty('branch'))
                    .replace('/', '_').replace('-', '_') +
                    '" --host ' + coverity_server + ' --user ' + username +
                    ' --password ' + user_pwd), haltOnFailure=True,
                logfile='stdio'),

            util.ShellArg(
                command=str('cd ' + repo_dir), haltOnFailure=True,
                logfile='stdio'),

            util.ShellArg(
                command=str('cov-build --dir ' + os.path.join(
                    build_dir, self.getProperty('project').replace('/', '_'),
                    self.getProperty('branch').replace('/', '_')
                    .replace('-', '_')) + ' ' + command),
                haltOnFailure=True, logfile='stdio'),

            util.ShellArg(
                command=str('cov-analyze --dir ' + os.path.join(
                    build_dir, self.getProperty('project').replace('/', '_'),
                    self.getProperty('branch').replace('/', '_')
                    .replace('-', '_')) + ' --' + langage +
                    ' --concurrency --strip-path ' + repo_dir),
                haltOnFailure=True, logfile='stdio'),

            util.ShellArg(
                command=str(
                    'cov-commit-defects --description "' +
                    self.getProperty('b4nb') +
                    '" --host ' + coverity_server + ' --dataport ' +
                    data_port + ' --stream '
                    + (self.getProperty('project') + '_'
                       + self.getProperty('branch')).replace('/', '_')
                    .replace('-', '_') + ' --dir ' + os.path.join(
                        build_dir, self.getProperty('project').
                        replace('/', '_'), self.getProperty('branch').
                        replace('/', '_').replace('-', '_')) + ' --user ' +
                    username + ' --password '
                    + user_pwd + ' --scm ' + scm),
                haltOnFailure=False, logfile='stdio')
        ]

        return commands
