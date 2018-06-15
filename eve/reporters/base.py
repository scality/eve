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
"""Allow eve to send reports."""

import re

from buildbot.process.results import (CANCELLED, EXCEPTION, FAILURE, RETRY,
                                      SKIPPED, SUCCESS, WARNINGS, Results)
from buildbot.reporters import utils
from buildbot.reporters.http import HttpStatusPushBase
from twisted.internet import defer

REPO_ICON = 'http://www.packal.org/sites/default/files/public/styles/icon_' \
            'large/public/workflow-files/netdeanishealfred-git-repos/icon/' \
            'icon.png?itok=1zkuMgPa'
BRANCH_ICON = 'http://plainicon.com/dboard/userprod/2800_a1826/prod_thumb/' \
              'plainicon.com-50219-512px-201.png'
CLOCK_ICON = 'https://image.freepik.com/free-icon/clock-of-circular-shape-at' \
             '-two-o-clock_318-48022.jpg'


class BaseBuildStatusPush(HttpStatusPushBase):
    """Base class for pushing build status."""

    repo = None
    neededDetails = dict(wantProperties=True, wantSteps=True)
    RESULT_COLOR_CORRESP = {
        SUCCESS: 'green',
        WARNINGS: 'orange',
        FAILURE: 'red',
        SKIPPED: 'white',
        EXCEPTION: 'purple',
        RETRY: 'purple',
        CANCELLED: 'pink',
    }

    @defer.inlineCallbacks
    def getDetailsForTriggeredBuilds(self, build):  # noqa
        """Get details for triggered builds."""
        for step in build['steps']:
            step.setdefault('triggered_builds', [])
            for url in step['urls']:
                matched = re.search(r'builders/(\d+)/builds/(\d+)', url['url'])
                if not matched:
                    continue
                builds = self.master.db.builds
                trig_build = yield builds.getBuildByNumber(*matched.groups())
                trig_build['buildid'] = trig_build['id']
                yield utils.getDetailsForBuild(self.master,
                                               trig_build,
                                               **self.neededDetails)
                yield self.getDetailsForTriggeredBuilds(trig_build)
                step['triggered_builds'].append(trig_build)

    @defer.inlineCallbacks
    def getMoreInfoAndSend(self, build):  # noqa
        yield utils.getDetailsForBuild(self.master, build,
                                       **self.neededDetails)
        if self.filterBuilds(build):
            yield self.getDetailsForTriggeredBuilds(build)
            yield self.send(build)

    def gather_data(self, build):
        """Gathers data to be used in build status.

        Args:
            build (dict): The build dictionary.

        Returns:
            dict: (key, result, title, summary, description).

        """
        key = build['properties']['stage_name'][0]
        src = build['buildset']['sourcestamps'][0]
        self.repo = src['repository'].strip('/').split('/')[-1].replace(
            '.git', '')
        branch = src['branch']
        title = 'build #%s' % build['buildid']
        summary = '(%s) build #%s on %s:%s ' % (
            build['state_string'], build['buildid'], self.repo, branch)

        self.add_tag('branch', branch, BRANCH_ICON, color='blue')
        self.add_tag('repository', self.repo, REPO_ICON, color='blue')

        result = build['results']
        description = 'in progress...'
        if result is not None:
            description = 'Hooray!'
            duration = build['complete_at'] - build['started_at']
            # Workaround: `complete_at` and `started_at` may be an int or
            # a datetime.timedelta, below we convert it to a int in any case.
            try:
                duration = duration.seconds
            except AttributeError:
                pass
            summary += '[%s]' % Results[result]
            if result != SUCCESS:
                description = Results[result] + ' in step(s): ' + ', '.join(
                    self.getStepsWithResult(build))

            self.add_tag('result', Results[result], None,
                         color=self.RESULT_COLOR_CORRESP[result])
            self.add_tag('duration', '%d seconds' % duration, CLOCK_ICON,
                         color='gray')

        return key, result, title, summary, description

    def getStepsWithResult(self, build):  # noqa
        """Get steps with result."""
        res = []
        for step in build['steps']:
            if step['results'] != build['results']:
                continue
            if step.get('triggered_builds'):
                for trig_build in step['triggered_builds']:
                    if trig_build['results'] != build['results']:
                        continue
                    for step_chain in self.getStepsWithResult(trig_build):
                        stage_name = trig_build['properties']['stage_name'][0]
                        res.append('%s -> %s' % (stage_name, step_chain))
            else:
                res.append(step['name'])
        return res

    def add_tag(self, name, value, icon, color=None):
        """Add a tag (name, value) to the status.

        Args:
            name (str): The name of the tag.
            value (str): The value of the tag.
            icon (str): A square image url (can be None) (HipChat Only).
            color (str): The color of the tag (HipChat Only).

        """
        raise NotImplementedError()

    def filterBuilds(self, build):
        """Tell if the result of the stage (aka build) should be reported.

        This overrides entirely Buildbot's default `filterBuilds`.

        Currently Eve only reports build statuses for the master
        build (i.e. the top stage selected to run during bootstrap).

        If the parent build is bootstrap: report build status (True)
        If the parent build is something else (lower stage): block (False)

        We identify the parent build by reading property `reason`, which
        contains the string "triggered by bootstrap" if and only if
        the stage has been triggered by bootstrap.

        Args:
            build: The build running the stage.

        """
        return build['properties']['reason'][0].endswith(
            '(triggered by bootstrap)')
