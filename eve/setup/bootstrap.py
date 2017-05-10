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

from buildbot.config import BuilderConfig
from buildbot.plugins import steps, util
from buildbot.process.factory import BuildFactory
from buildbot.process.properties import Property
from buildbot.process.results import SKIPPED, SUCCESS
from buildbot.steps.master import SetProperty
from buildbot.steps.shell import SetPropertyFromCommand
from buildbot.steps.source.git import Git


def bootstrap_builder(workers):
    bootstrap_factory = BuildFactory()

    if util.env.RAX_LOGIN:
        bootstrap_factory.addStep(
            steps.CloudfilesAuthenticate(
                rax_login=util.env.RAX_LOGIN,
                rax_pwd=util.env.RAX_PWD))

    git_config = None

    if util.env.GITCACHE_IN_USE:
        bootstrap_factory.addStep(steps.CheckGitCachePresence())

    #   gitcache = util.env.GITCACHE_HOSTNAME
    #   git_config = {
    #       'url.http://{}/https/bitbucket.org/.insteadOf'.format(gitcache):
    #           'git@bitbucket.org:',
    #       'url.http://{}/https/github.com/.insteadOf'.format(gitcache):
    #           'git@github.com:',
    #       'url.http://{}/git/.insteadOf'.format(gitcache):
    #           'git://'
    #   }

    # The code commented above will only work when we have full dockerization,
    # and bootstrap runs in a docker linked to gitcache. In the meantime, we
    # live without a cache on 'backend' machines (acceptable for the small
    # repos # only; already deployed without cache on current production eve
    # 1.2b1)

    bootstrap_factory.addStep(
        Git(name='checkout git branch',
            repourl=util.env.GIT_REPO,
            retry=(60, 10),
            submodules=True,
            branch=Property('branch'),
            mode='incremental',
            hideStepIf=lambda results, s: results == SUCCESS,
            haltOnFailure=True,
            config=git_config))

    bootstrap_factory.addStep(steps.CancelNonTipBuild())

    bootstrap_factory.addStep(
        SetProperty(
            name='setting the master_builddir property',
            property='master_builddir',
            hideStepIf=lambda results, s: results == SUCCESS,
            value=Property('builddir')))

    # Read patcher conf and populate related properties
    bootstrap_factory.addStep(
        steps.StepPatcherConfig(
            conf_path=util.env.PATCHER_FILE_PATH,
            name='check if any steps should currently be patched',
            doStepIf=bool(util.env.PATCHER_FILE_PATH),
            hideStepIf=lambda results, s: results in (SUCCESS, SKIPPED)))

    bootstrap_factory.addStep(SetProperty(
        name='get the git host',
        property='git_host',
        hideStepIf=lambda results, s: results == SUCCESS,
        value=util.env.GIT_HOST))

    bootstrap_factory.addStep(SetProperty(
        name='get the git owner',
        property='git_owner',
        hideStepIf=lambda results, s: results == SUCCESS,
        value=util.env.GIT_OWNER))

    bootstrap_factory.addStep(SetProperty(
        name='get the repository name',
        property='git_slug',
        hideStepIf=lambda results, s: results == SUCCESS,
        value=util.env.GIT_SLUG))

    bootstrap_factory.addStep(SetPropertyFromCommand(
        name='get the product version',
        command=('./eve/get_product_version.sh 2> /dev/null'
                 ' || echo 0.0.0'),
        hideStepIf=lambda results, s: results == SUCCESS,
        property='product_version'))

    # Read conf from yaml file
    bootstrap_factory.addStep(steps.ReadConfFromYaml())

    return BuilderConfig(
        name=util.env.BOOTSTRAP_BUILDER_NAME,
        workernames=[lw.name for lw in workers],
        factory=bootstrap_factory,
        properties={
            'artifacts_url': util.env.ARTIFACTS_URL,
            'artifacts_prefix': util.env.ARTIFACTS_PREFIX,
        },
    )
