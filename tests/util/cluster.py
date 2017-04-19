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
        return 'git://{}:{}/repo_owner/test.git'.format(
            self.external_ip, self.githost.port)

    def clone(self):
        return LocalGitRepo(remote=self.githost_url)

    @property
    def external_ip(self):
        return 'localhost'

    @property
    def db_url(self):
        return self.database.url

    @property
    def external_url(self):
        return self._first_frontend.external_url

    def add_master(self, mode):
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
        self.githost.start()
        self._crossbar.start()
        self.database.start()
        for master in self._masters.values():
            master.start()
        return self

    def stop(self):
        self.githost.stop()
        for master in self._masters.values():
            master.stop()
        self._crossbar.stop()
        return self

    def delete_master(self, name):
        self._masters[name].stop()

    @property
    def first_master(self):
        return self._masters.values()[0]

    @property
    def api(self):
        return self.first_master.api

    def webhook(self, git_repo):
        return self.api.webhook(git_repo)

    def force(self, branch):
        return self.api.force(branch)

    def sanity_check(self):
        for master in self._masters.values():
            master.sanity_check()

    def __delete__(self, _):
        self.stop()
        del self._crossbar
        for master in self._masters.values():
            del master
