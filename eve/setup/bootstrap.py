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

from os.path import dirname, isfile

from buildbot.config import BuilderConfig
from buildbot.plugins import steps, util
from buildbot.process.factory import BuildFactory
from buildbot.process.properties import Property
from buildbot.steps.master import SetProperty
from buildbot.steps.shell import SetPropertyFromCommand
from buildbot.steps.source.git import Git
from twisted.internet import defer


# Do not build if NO_NEW_BUILD_FILE_PATH exists
@defer.inlineCallbacks
def eve_canStartBuild(builder, wfb, request):
    yield
    if isfile(util.env.NO_NEW_BUILD_FILE_PATH):
        defer.returnValue(False)
    defer.returnValue(True)


def bootstrap_builder(workers):
    bootstrap_factory = BuildFactory()

    if util.env.RAX_LOGIN:
        bootstrap_factory.addStep(
            steps.CloudfilesAuthenticate(
                rax_login=util.env.RAX_LOGIN,
                rax_pwd=util.env.RAX_PWD))

    bootstrap_factory.addStep(
        Git(name='checkout git branch',
            repourl=util.env.GIT_REPO,
            retry=(60, 10),
            submodules=True,
            branch=Property('branch'),
            mode='incremental',
            hideStepIf=util.hideStepIfSuccess,
            haltOnFailure=True))

    bootstrap_factory.addStep(steps.CancelNonTipBuild())

    bootstrap_factory.addStep(
        SetProperty(
            name='setting the master_builddir property',
            property='master_builddir',
            hideStepIf=util.hideStepIfSuccess,
            value=Property('builddir')))

    # Read patcher conf and populate related properties
    bootstrap_factory.addStep(
        steps.StepPatcherConfig(
            conf_path=util.env.PATCHER_FILE_PATH,
            name='check if any steps should currently be patched',
            doStepIf=bool(util.env.PATCHER_FILE_PATH),
            hideStepIf=util.hideStepIfSuccessOrSkipped))

    bootstrap_factory.addStep(SetProperty(
        name='get the git host',
        property='git_host',
        hideStepIf=util.hideStepIfSuccess,
        value=util.env.GIT_HOST))

    bootstrap_factory.addStep(SetProperty(
        name='get the git owner',
        property='git_owner',
        hideStepIf=util.hideStepIfSuccess,
        value=util.env.GIT_OWNER))

    bootstrap_factory.addStep(SetProperty(
        name='get the repository name',
        property='git_slug',
        hideStepIf=util.hideStepIfSuccess,
        value=util.env.GIT_SLUG))

    yaml_dirpath = dirname(util.env.PROJECT_YAML)
    bootstrap_factory.addStep(SetPropertyFromCommand(
        name='get the product version',
        command=('./{}/get_product_version.sh 2> /dev/null'
                 ' || echo 0.0.0'.format(yaml_dirpath)),
        hideStepIf=util.hideStepIfSuccess,
        property='product_version'))

    # Read conf from yaml file
    bootstrap_factory.addStep(
        steps.ReadConfFromYaml(name='read %s' % util.env.PROJECT_YAML,
                               yaml=util.env.PROJECT_YAML))

    return BuilderConfig(
        name=util.env.BOOTSTRAP_BUILDER_NAME,
        workernames=[lw.name for lw in workers],
        factory=bootstrap_factory,
        properties={
            'artifacts_url': util.env.ARTIFACTS_URL,
            'artifacts_prefix': util.env.ARTIFACTS_PREFIX,
        },
        canStartBuild=eve_canStartBuild,
        nextBuild=util.nextBootstrapBuild,
    )
