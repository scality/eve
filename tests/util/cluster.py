"""
Tools to configure and interact with a testing eve cluster
"""
from collections import OrderedDict

from tests.util.buildbot_master import BuildbotMaster
from tests.util.crossbar.crossbar import Crossbar
from tests.util.git.git_repo import LocalGitRepo
from tests.util.githost_mock.githost_mock import GitHostMock
from tests.util.sqlite import Sqlite


class Cluster(object):
    cluster_count = 0
    database = None
    githost_class = GitHostMock
    db_class = Sqlite
    crossbar_class = Crossbar
    buildbot_master_class = BuildbotMaster

    def __init__(self, githost=None):
        """
        Configure and interact with a testing eve cluster

        Args:
            githost (GitHostMock): optional parameter to specify the git host
                                   that will be used to fake bitbucket or
                                   github. The default is specified by
                                   self.githost_class.
        """
        self.githost = githost if githost is not None else self.githost_class()

        self._crossbar = self.crossbar_class()

        self.wamp_url = 'ws://{}:{}/ws'.format(self.external_ip,
                                               self._crossbar.port)

        self.database = self.db_class(external_ip=self.external_ip)

        self._masters = OrderedDict()

        self._first_frontend = self.buildbot_master_class(
            'frontend',
            db_url=self.database.url,
            git_repo=self.githost_url,
            master_fqdn=self.external_ip,
            wamp_url=self.wamp_url)
        self._masters[self._first_frontend._name] = self._first_frontend

        self.add_master('backend')

    @property
    def githost_url(self):
        """
        Generates the url that points to the git repo.
        """
        return 'git://{}:{}/repo_owner/test.git'.format(
            self.external_ip, self.githost.port)

    def clone(self):
        """
        clones the git repo from the githost to a local directory

        Returns: LocalGitRepo object

        """
        return LocalGitRepo(remote=self.githost_url)

    @property
    def external_ip(self):
        """
        Returns: the external IP of the cluster.

        """
        return 'localhost'

    @property
    def db_url(self):
        """
        Returns: the sqlachemy URL of the database of the cluster

        """
        return self.database.url

    @property
    def external_url(self):
        """
        Returns: the external web url of the cluster

        """
        return self._first_frontend.external_url

    def add_master(self, mode):
        """
        Add a master to the cluster

        Args:
            mode (string): frontend/backend/standalone/symmetric

        Returns: a freshly created self.master_class object

        """
        master = self.buildbot_master_class(
            mode,
            git_repo=self.githost_url,
            external_url=self.external_url,
            db_url=self.db_url,
            master_fqdn=self.external_ip,
            wamp_url=self.wamp_url, )
        self._masters[master._name] = master
        return master

    def start(self):
        """
        Start the cluster (blocking)

        Returns: the cluster instance

        """
        self.githost.start()
        self._crossbar.start()
        self.database.start()
        for master in self._masters.values():
            master.start()
        return self

    def stop(self):
        """
        Stop the cluster (blocking)

        Returns: the cluster instance

        """
        self.githost.stop()
        for master in self._masters.values():
            master.stop()
        self._crossbar.stop()
        return self

    @property
    def first_master(self):
        """
        Returns: the first master of the cluster. Usually a frontend.

        """
        return self._masters.values()[0]

    @property
    def api(self):
        """
        Returns: the API object that allows to interact with this cluster.

        """
        return self.first_master.api

    def webhook(self, git_repo):
        return self.api.webhook(git_repo)

    def force(self, branch):
        """
        Forces a build from the API

        Args:
            branch (str): The remote branch to be built

        Returns: An API BuildSet object

        """
        return self.api.force(branch)

    def sanity_check(self):
        """
        Check that the cluster has no unexpected error messages in logs.
        """
        for master in self._masters.values():
            master.sanity_check()

    def __delete__(self, _):
        """
        delete the cluster
        Args:
            _: ignored
        """
        self.stop()
        del self._crossbar
        for master in self._masters.values():
            del master
