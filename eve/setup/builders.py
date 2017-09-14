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
from buildbot.steps.shell import ShellCommand


def triggerable_builder(builder_name, workers):
    factory = BuildFactory()
    factory.addStep(steps.CancelOldBuild(name='prevent unuseful restarts'))
    factory.addStep(steps.SetArtifactsPrivateURL(
        builder_name == util.env.OPENSTACK_BUILDER_NAME))

    # customize global Git conf to hit on docker cache
    if (util.env.MICROSERVICE_GITCACHE_IN_USE and
            builder_name == util.env.DOCKER_BUILDER_NAME):
        factory.addStep(ShellCommand(
            name='customize git settings to hit on cache',
            hideStepIf=util.hideStepIfSuccess,
            haltOnFailure=True,

            command='git config --global '
                    'url.http://gitcache/https/bitbucket.org/.insteadOf '
                    'git@bitbucket.org: && '
                    'git config --global '
                    'url.http://gitcache/https/github.com/.insteadOf '
                    'git@github.com: && '
                    'git config --global '
                    'url.http://gitcache/git/mock/.insteadOf git@mock: && '
                    'git config --global '
                    'lfs.url '
                    '"http://gitcache:81/'
                    '%(githost)s/%(gitowner)s/%(gitslug)s.git/info/lfs"' % {
                        'githost': util.env.GIT_HOST,
                        'gitowner': util.env.GIT_OWNER,
                        'gitslug': util.env.GIT_SLUG
                    },
        ))

    # Extract steps from conf
    factory.addStep(steps.StepExtractor(
        name='extract steps from yaml',
        hideStepIf=util.hideStepIfSuccess
    ))

    return BuilderConfig(
        name=builder_name,
        workernames=[w.name for w in workers],
        factory=factory,
        collapseRequests=False)
