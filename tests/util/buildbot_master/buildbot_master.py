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

from __future__ import print_function

import os
from os.path import join
from shutil import copy

import yaml

from tests.util.buildbot_api_client import BuildbotDataAPI
from tests.util.cmd import cmd
from tests.util.daemon import Daemon


class BuildbotMaster(Daemon):
    _start_wait = 600
    _log = 'twistd.log'
    _start_cmd = ['buildbot', 'start', '.']
    _stop_cmd = 'buildbot stop --no-wait .'
    _env = None

    def __init__(self, conf):
        """Class representing a Buildbot Daemon.

        Args:
            conf (dict): eve settings.

        """
        self.conf = conf
        super(BuildbotMaster, self).__init__(name=self.conf['MASTER_NAME'])
        self.start_success_msg = 'BuildMaster is running'
        self.api = BuildbotDataAPI(self.conf['EXTERNAL_URL'])

    def pre_start_hook(self):
        """Dump conf and launch the 'create-master' command before starting."""
        master_cfg = join('eve', 'etc', 'master.cfg')
        copy(master_cfg, join(self._base_path, 'master.cfg'))

        cmd('buildbot create-master --relocatable --db={} {}'.format(
            self.conf['DB_URL'], self._base_path))

        self._env = self.environ

    def sanity_check(self):
        """Check that the buildmaster has no unexpected error msgs in logs."""
        loglines = self.loglines
        for i, logline in enumerate(loglines):
            if 'Traceback' in logline:
                try:
                    if 'jwt.exceptions.DecodeError' in loglines[i + 1]:
                        # ignore JWT http token exception.
                        continue
                except IndexError:
                    pass
                self.print_loglines()
                raise RuntimeError(
                    'Found a traceback in log of {}'.format(self._name))
            if 'Stopping factory <autobahn.twisted' in logline:
                self.print_loglines()
                raise RuntimeError(
                    '{} has lost connection to crossbar'.format(self._name))
            if 'Configuration Errors:' in logline:
                self.print_loglines()
                raise RuntimeError(
                    '{} has lost configuration errors'.format(self._name))

    def add_conf_file(self, yaml_data, filename):
        """Add configuration files to the master's directory.

        Args:
            yaml_data (dict): The contents of the conf file.
            filename (str): The path to the conf file.

        """
        abspath = os.path.join(self._base_path, filename)
        pardir = os.path.abspath(os.path.join(abspath, os.pardir))
        if not os.path.exists(pardir):
            os.makedirs(pardir)
        with open(abspath, 'w') as fhandle:
            yaml.dump(yaml_data, fhandle, default_flow_style=False)

    @property
    def environ(self):
        """Return the environment that the buildmaster will run with."""
        env = os.environ.copy()
        for key, value in self.conf.items():
            env[key] = value
        return env

    def dump(self, filename):
        """Dump the buildmaster's conf.

        Args:
            filename: The path to the conf file.

        """
        with open(filename, 'w') as fhandle:
            lines = [
                '{}={}\n'.format(key, value)
                for (key, value) in self.conf.items()
            ]
            fhandle.writelines(lines)
