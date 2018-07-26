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
from buildbot.steps.shell import ShellCommand
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

    bootstrap_factory.addStep(
        steps.EveProperty(
            name='set the bootstrap build number',
            property='bootstrap',
            hideStepIf=util.hideStepIfSuccess,
            value=Property('buildnumber')))

    bootstrap_factory.addStep(ShellCommand(
        name='check index.lock',
        command='test ! -f .git/index.lock',
        hideStepIf=util.hideStepIfSuccess,
        haltOnFailure=True,
        logEnviron=False))

    bootstrap_factory.addStep(
        Git(name='checkout git branch',
            repourl=util.env.GIT_REPO,
            retry=(60, 10),
            submodules=True,
            branch=Property('branch'),
            mode='full',
            method='fresh',
            hideStepIf=util.hideStepIfSuccess,
            haltOnFailure=True,
            logEnviron=False))

    bootstrap_factory.addStep(steps.CancelNonTipBuild(
        name='cancel builds for commits that are not branch tips',
        logEnviron=False))

    bootstrap_factory.addStep(
        steps.EveProperty(
            name='set the master_builddir property',
            property='master_builddir',
            hideStepIf=util.hideStepIfSuccess,
            value=Property('builddir')))

    yaml_dirpath = dirname(util.env.PROJECT_YAML)
    bootstrap_factory.addStep(steps.EvePropertyFromCommand(
        name='get the product version',
        command=('./{}/get_product_version.sh 2> /dev/null'
                 ' || echo 0.0.0'.format(yaml_dirpath)),
        hideStepIf=util.hideStepIfSuccess,
        property='product_version',
        logEnviron=False))

    # Read conf from yaml file
    bootstrap_factory.addStep(
        steps.ReadConfFromYaml(name='read %s' % util.env.PROJECT_YAML,
                               yaml=util.env.PROJECT_YAML))

    return BuilderConfig(
        name=util.env.BOOTSTRAP_BUILDER_NAME,
        workernames=[lw.name for lw in workers],
        factory=bootstrap_factory,
        canStartBuild=eve_canStartBuild,
        nextBuild=util.nextBootstrapBuild,
        properties={
            'git_host': util.env.GIT_HOST,
            'git_owner': util.env.GIT_OWNER,
            'git_slug': util.env.GIT_SLUG,
            'max_step_duration': util.env.MAX_STEP_DURATION,
            'stage_name': 'bootstrap',
        }
    )
