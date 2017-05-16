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
from buildbot.process.results import SUCCESS
from buildbot.steps.shell import ShellCommand


def triggerable_builder(builder_name, workers):
    factory = BuildFactory()
    factory.addStep(steps.CancelOldBuild())

    # customize global Git conf to hit on docker cache
    if (util.env.GITCACHE_IN_USE and
            builder_name == util.env.DOCKER_BUILDER_NAME):
        factory.addStep(ShellCommand(
            name='customize git settings to hit on cache',
            hideStepIf=lambda results, s: results == SUCCESS,
            haltOnFailure=True,

            command='git config --global '
                    'url.http://%(gitcache)s/https/bitbucket.org/.insteadOf '
                    'git@bitbucket.org: && '
                    'git config --global '
                    'url.http://%(gitcache)s/https/github.com/.insteadOf '
                    'git@github.com: && '
                    'git config --global '
                    'url.http://%(gitcache)s/git/mock/.insteadOf git@mock: && '
                    'git config --global '
                    'lfs.url '
                    '"http://%(gitcache)s:81/'
                    '%(githost)s/%(gitowner)s/%(gitslug)s.git/info/lfs"' % {
                        'gitcache': util.env.GITCACHE_HOSTNAME,
                        'githost': util.env.GIT_HOST,
                        'gitowner': util.env.GIT_OWNER,
                        'gitslug': util.env.GIT_SLUG
                    },
        ))

    # Extract steps from conf
    factory.addStep(steps.StepExtractor(
        name='extract steps from yaml',
        hideStepIf=lambda results, s: results == SUCCESS
    ))

    return BuilderConfig(
        name=builder_name,
        workernames=[w.name for w in workers],
        factory=factory,
        collapseRequests=False)
