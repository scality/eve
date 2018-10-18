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
"""Tools to configure and interact with a testing eve cluster."""

from collections import OrderedDict

from tests.util.buildbot_master import BuildbotMaster
from tests.util.crossbar.crossbar import Crossbar
from tests.util.daemon import Daemon
from tests.util.git.git_repo import LocalGitRepo
from tests.util.githost_mock.githost_mock import GitHostMock
from tests.util.sqlite import Sqlite


class Cluster(object):
    database = None
    githost_class = GitHostMock
    db_class = Sqlite
    crossbar_class = Crossbar
    buildbot_master_class = BuildbotMaster
    registry_class = None
    _first_frontend = None

    def __init__(self, githost=None, backends=1, extra_conf=None):
        """Configure and interact with a testing eve cluster.

        Args:
            githost (GitHostMock): Optional parameter to specify the git host
                that will be used to fake bitbucket or github. The default is
                specified by self.githost_class.
            extra_conf (dict): additional env values.

        """
        extra_conf = extra_conf or {}
        self._masters = OrderedDict()

        self.githost = githost if githost is not None else self.githost_class()
        self._crossbar = self.crossbar_class()
        self.database = self.db_class(external_ip=self.external_ip)

        self.vault = None
        if extra_conf.get('VAULT_IN_USE', None) == '1':
            self.vault = self.add_vault()

        self.registry = None
        if extra_conf.get('DOCKER_REGISTRY_URL', None) == 'mock':
            assert self.registry_class is not None
            # pylint: disable=not-callable
            self.registry = self.registry_class(external_ip=self.external_ip)
            # remove so that it can populated with correct URL later:
            extra_conf.pop('DOCKER_REGISTRY_URL')

        self._first_frontend = self.add_master(
            mode='frontend', extra_conf=extra_conf)

        for _ in range(backends):
            self.add_master(mode='backend', extra_conf=extra_conf)

    def __enter__(self):
        return self.start()

    def __exit__(self, type, value, traceback):
        self.stop()

    def __repr__(self):
        return 'Cluster {}'.format(self.api.url)

    @property
    def githost_url(self):
        """Generate the url that points to the git repo."""
        return 'git://{}:{}/repo_owner/test.git'.format(
            self.external_ip, self.githost.port)

    def clone(self):
        """Clone the git repo from the githost to a local directory.

        Returns:
            LocalGitRepo: The.repository's local clone.

        """
        return LocalGitRepo(remote=self.githost_url)

    @property
    def external_ip(self):
        """Return the external IP of the cluster."""
        return 'localhost'

    @property
    def db_url(self):
        """Return the sqlachemy URL of the database of the cluster."""
        return self.database.url

    @property
    def external_url(self):
        """Return the external web url of the cluster."""
        return self._first_frontend.conf['EXTERNAL_URL']

    def add_vault(self):
        return None

    default_conf = dict(
        ARTIFACTS_PUBLIC_URL='None',
        DOCKER_API_VERSION='1.25',
        DOCKER_REGISTRY_URL='',
        GIT_HOST='mock',
        GIT_OWNER='repo_owner',
        GIT_SLUG='test',
        HIDE_INTERNAL_STEPS='0',
        MAX_LOCAL_WORKERS='4',
        PROJECT_URL='www.example.com',
        PROJECT_YAML='eve/main.yml',
        SUFFIX='test_suffix',
        VAULT_IN_USE='0',
        WAMP_REALM='realm1',
        WORKER_SUFFIX='test-eve',
    )

    def build_conf(self, mode, extra_conf=None):
        conf = {}
        extra_conf = extra_conf or {}

        def setdef(item, value):
            conf[item] = extra_conf.get(item, str(value))

        if not self._first_frontend:
            # master #1 in cluster, create a new default conf
            conf = dict(self.default_conf)
        else:
            # master #2+, reuse conf from first master
            conf = dict(self._first_frontend.conf)

        # set values that must be unique per master
        ports = Daemon.get_free_port(3)
        setdef('HTTP_PORT', 'tcp:%d' % ports[0])
        setdef('PB_PORT', ports[1])
        setdef('TRY_PORT', ports[2])
        setdef('MASTER_MODE', mode)
        setdef('MASTER_NAME', '%s%d' % (mode, ports[0]))
        setdef('MASTER_FQDN', self.external_ip)

        # this part adds dynamic values to the default conf
        if not self._first_frontend:
            setdef('WAMP_ROUTER_URL', 'ws://{}:{}/ws'.format(
                self.external_ip,
                self._crossbar.port
            ))
            setdef('DB_URL', self.database.url)
            if self.vault:
                setdef('VAULT_URL', self.vault.url)
            if self.registry:
                setdef('DOCKER_REGISTRY_URL', 'localhost:{}'.format(
                    self.registry.port
                ))

            setdef('GIT_REPO', self.githost_url)

            setdef('EXTERNAL_URL', 'http://%s:%d/' % (
                   self.external_ip, ports[0]))

        # apply requested personalisations
        for entry, value in extra_conf.iteritems():
            conf[entry] = value

        return conf

    def add_master(self, mode, extra_conf=None):
        """Add a master to the cluster.

        Args:
            mode (string): Any of frontend/backend/standalone/symmetric.

        Returns:
            A freshly created self.master_class object.

        """
        master = self.buildbot_master_class(
            conf=self.build_conf(mode, extra_conf)
        )
        self._masters[master._name] = master
        return master

    def start(self):
        """Start the cluster (blocking).

        Returns:
            The cluster instance.

        """
        self.githost.start()
        self._crossbar.start()
        self.database.start()
        if self.vault:
            self.vault.start()
            # special case: token can be only be obtained
            # when vault has already started
            token = self.vault.token
            for master in self._masters.values():
                master.conf.setdefault('VAULT_TOKEN', token)
        if self.registry:
            self.registry.start()
        for master in self._masters.values():
            master.start()
        return self

    def stop(self):
        """Stop the cluster (blocking).

        Returns:
            The cluster instance.

        """
        for master in self._masters.values():
            master.stop()
        if self.registry:
            self.registry.stop()
        if self.vault:
            self.vault.stop()
        self.database.stop()
        self._crossbar.stop()
        self.githost.stop()
        return self

    @property
    def first_master(self):
        """Return the first master of the cluster. Usually a frontend."""
        return self._masters.values()[0]

    @property
    def api(self):
        """Return the API object that allows to interact with this cluster."""
        return self.first_master.api

    def webhook(self, git_repo, revision=None):
        return self.api.webhook(git_repo, revision)

    def sanity_check(self):
        """Check that the cluster has no unexpected error messages in logs."""
        for master in self._masters.values():
            master.sanity_check()

    def __delete__(self, _):
        """Delete the cluster.

        Args:
            _: Ignored.

        """
        self.stop()
        del self._crossbar
        for master in self._masters.values():
            del master
