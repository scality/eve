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
    _start_cmd = ['buildbot', 'start', '--nodaemon', '.']
    _stop_cmd = 'buildbot stop --no-wait .'
    _env = None

    def __init__(self,
                 mode,
                 git_repo,
                 external_url=None,
                 db_url=None,
                 master_fqdn='localhost',
                 wamp_url=None):
        """
        Class representing a Buildbot Daemon

        Args:
            mode (str): frontend/backend/standalone/symmetric
            git_repo (GitHostMock): The remote git repo to use
            external_url: The external web url
            db_url: The sqlalchemy url to connect to
            master_fqdn: the FQDN of the master so the workers can connect to.
            wamp_url: The url to the wamp router
        """
        self.http_port = self.get_free_port()
        name = '{}{}'.format(mode, self.http_port)
        super(BuildbotMaster, self).__init__(name=name)

        self.external_url = external_url if external_url is not None else \
            'http://localhost:%s/' % str(self.http_port)

        self.db_url = db_url if db_url is not None else \
            'sqlite:///' + os.path.join(self._base_path, 'state.sqlite')

        max_local_workers = 4

        self.conf = dict(
            MASTER_NAME=name,
            HTTP_PORT=str(self.http_port),
            PB_PORT=str(self.get_free_port()),
            TRY_PORT=str(self.get_free_port()),
            EXTERNAL_URL=str(self.external_url),
            MASTER_FQDN=master_fqdn,
            WORKER_SUFFIX='test-eve',
            MAX_LOCAL_WORKERS=str(max_local_workers),
            MASTER_MODE=mode,
            WAMP_REALM='realm1',
            ARTIFACTS_URL='None',
            CLOUDFILES_URL='None',
            DOCKER_API_VERSION='1.25',
            GIT_HOST='mock',
            GIT_SLUG='test',
            GIT_OWNER='repo_owner',
            GIT_REPO=git_repo,
            # GIT_REPO='git@mock:repo_owner/test.git',
            PROJECT_URL='www.example.com',
            PROJECT_YAML='eve/main.yml',
            SECRET_ARTIFACT_CREDS='None',
            SUFFIX='test_suffix',
            DB_URL=self.db_url, )

        if wamp_url:
            self.conf['WAMP_ROUTER_URL'] = wamp_url

        self.start_success_msg = 'BuildMaster is running'
        self.api = BuildbotDataAPI(self.external_url)

    def pre_start_hook(self):
        """
        Dump conf and launch the 'create-master' command before starting
        """
        master_cfg = join('eve', 'etc', 'master.cfg')
        copy(master_cfg, join(self._base_path, 'master.cfg'))

        cmd('buildbot create-master --relocatable --db={} {}'.format(
            self.db_url, self._base_path))
        import pprint
        pprint.pprint(self.environ)
        self._env = self.environ

    def sanity_check(self):
        """
        Check that the buildmaster has no unexpected error messages in logs.
        """
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

    def add_conf_file(self, yaml_data, filename):
        """
        Add configuration files to the master's directory

        Args:
            yaml_data (dict): the contents of the conf file
            filename: the path to the conf file
        """
        abspath = os.path.join(self._base_path, filename)
        pardir = os.path.abspath(os.path.join(abspath, os.pardir))
        if not os.path.exists(pardir):
            os.makedirs(pardir)
        with open(abspath, 'w') as fhandle:
            yaml.dump(yaml_data, fhandle, default_flow_style=False)

    @property
    def environ(self):
        """
        Returns: The environment that the buildmaster will run with

        """
        env = os.environ.copy()
        for key, value in self.conf.items():
            env[key] = value
        return env

    def dump(self, filename):
        """
        Dump the buildmaster's conf
        Args:
            filename: the path to the conf file
        """
        with open(filename, 'w') as fhandle:
            lines = [
                '{}={}\n'.format(key, value)
                for (key, value) in self.conf.items()
            ]
            fhandle.writelines(lines)
