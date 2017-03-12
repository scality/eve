from buildbot.process import buildrequest

from bugfixes.tempsourcestamp import TempSourceStamp
from setup import frontend_schedulers, git_poller, www


def setup_frontend_only(conf, git_repo, project_name, bootstrap_builder_name):

    www.setup_www(conf, bootstrap_builder_name)

    ##########################
    # Change Sources
    ##########################
    git_poller.setup_git_poller(conf, git_repo)

    # #########################
    # Collapsing requests
    # #########################
    conf['collapseRequests'] = False

    buildrequest.TempSourceStamp = TempSourceStamp

    # #########################
    # Bootstrap Sequence: Schedulers
    # #########################
    frontend_schedulers.setup_frontend_schedulers(conf, bootstrap_builder_name,
                                                  git_repo, project_name)
