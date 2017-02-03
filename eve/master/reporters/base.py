#!/usr/bin/env python


import re
from buildbot.process.results import (CANCELLED, EXCEPTION, FAILURE, RETRY,
SKIPPED, SUCCESS, WARNINGS, Results)
from buildbot.reporters import utils
from buildbot.reporters.http import HttpStatusPushBase
from buildbot.util.httpclientservice import HTTPClientService
from twisted.internet import defer
from twisted.logger import Logger


class BaseBuildStatusPush(HttpStatusPushBase):
    """
    Base class for pushing build status
    """
    neededDetails = dict(wantProperties=True, wantSteps=True)
    RESULT_COLOR_CORRESP = {
        SUCCESS: 'green',
        WARNINGS: 'orange',
        FAILURE: 'red',
        SKIPPED: 'white',
        EXCEPTION: 'purple',
        RETRY: 'purple',
        CANCELLED: 'pink'}

    @defer.inlineCallbacks
    def getDetailsForTriggeredBuilds(self, build):
        for step in build['steps']:
            step.setdefault('triggered_builds', [])
            for url in step['urls']:
                matched = re.search(r'builders/(\d+)/builds/(\d+)', url['url'])
                if not matched:
                    continue
                trig_build = yield self.master.db.builds.getBuildByNumber(*matched.groups())
                trig_build['buildid'] = trig_build['id']
                yield utils.getDetailsForBuild(self.master,
                                               trig_build,
                                               **self.neededDetails)
                yield self.getDetailsForTriggeredBuilds(trig_build)
                step['triggered_builds'].append(trig_build)

    @defer.inlineCallbacks
    def getMoreInfoAndSend(self, build):
        yield utils.getDetailsForBuild(self.master, build, **self.neededDetails)
        if self.filterBuilds(build):
            yield self.getDetailsForTriggeredBuilds(build)
            yield self.send(build)

    def gather_data(self, build):
        """
        Gathers data to be used in build status
        :param build: The build dictionary
        :return: (key, result, title, summary, description)
        """
        key = build['properties']['stage_name']
        src = build['buildset']['sourcestamps'][0]
        self.repo = src['repository'].strip('/').split('/')[-1].\
            replace('.git', '')
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
            summary += '[%s]' % Results[result]
            if result != SUCCESS:
                description = Results[result] + ' in step(s): ' + ', '.join(
                    self.getStepsWithResult(build))

            self.add_tag('result', Results[result], None,
                         color=self.RESULT_COLOR_CORRESP[result])
            self.add_tag('duration', '%d seconds' % duration, CLOCK_ICON,
                         color='gray')

        return key, result, title, summary, description

    def getStepsWithResult(self, build):
        res = []
        for step in build['steps']:
            if step['results'] != build['results']:
                continue
            if step.get('triggered_builds'):
                for trig_build in step['triggered_builds']:
                    if trig_build['results'] != build['results']:
                        continue
                    for step_chain in self.getStepsWithResult(trig_build):
                        res.append('%s -> %s' % (trig_build['properties']['stage_name'][0],
                                                 step_chain))
            else:
                res.append(step['name'])
        return res

    def add_tag(self, name, value, icon, color=None):
        """
        Add a tag (name+value) to the status
        :param name: The name of the tag
        :param value: The value of the tag
        :param icon: a square image url (can be None) (HipChat Only)
        :param color: The color of the tag (HipChat Only)
        :return: None
        """
        raise NotImplementedError()


class HipChatBuildStatusPush(BaseBuildStatusPush):
    """Send build result to HipChat build status API."""
    name = "HipChatBuildStatusPush"
    logger = Logger('eve.steps.HipChatBuildStatusPush')
    attributes = []
    COLOR_STYLE_CORRESP = {
        'green': 'lozenge-success',
        'orange': 'lozenge-current',
        'red': 'lozenge-error',
        'white': 'lozenge',
        'purple': 'lozenge-error',
        'pink': 'lozenge-error',
        'brown': 'lozenge-moved',
        'blue': 'lozenge-complete',
        'gray': 'lozenge'}
    HIPCHAT_COLOR_CORRESP = {
        SUCCESS: 'green',
        WARNINGS: 'yellow',
        FAILURE: 'red',
        SKIPPED: 'gray',
        EXCEPTION: 'purple',
        RETRY: 'purple',
        CANCELLED: 'gray',
        None: 'gray'}

    def add_tag(self, name, value, icon, color=None):
        attr = dict(label=name, value=dict(label=value))
        if color in self.COLOR_STYLE_CORRESP:
            attr['value']['style'] = self.COLOR_STYLE_CORRESP[color]
        if icon:
            attr['value']['icon'] = dict(url=icon)
        self.attributes.append(attr)

    @defer.inlineCallbacks
    def send(self, build):
        """Send build status to HipChat."""

        self.attributes = []
        key, result, title, summary, description = self.gather_data(build)

        headers = {
            'content-type': 'application/json',
            'authorization': 'Bearer %s' % HIPCHAT_TOKEN}

        card = dict(
            style='application',
            url=build['url'],
            format='medium',
            id=key,
            title=title,
            description=dict(format='text', value=description),
            attributes=self.attributes,
            activity=dict(html=summary))

        data = dict(
            message=summary,
            name=key,
            message_format='text',
            notify=True,
            card=card,
            color=self.HIPCHAT_COLOR_CORRESP[result])

        url = 'https://api.hipchat.com/v2/room/%s/notification' % HIPCHAT_ROOM

        if EVE_BITBUCKET_LOGIN == 'test':
            return  # Don't really push status for tests
        response = yield self.session.post(url, headers=headers, json=data)
        if response.status_code != 204:
            raise Exception(
                "{response.status_code}: unable to send status to HipChat: "
                "{url}\nRequest:\n{request}\nResponse:\n{response.content}".
                format(request=data, response=response, url=url))
        self.logger.info("HipChat status sent")

# The status push works only on the main builder (bootstrap)
# To reactivate when fixed
#EVE_CONF['services'].append(HipChatBuildStatusPush(
#    builders=[BOOTSTRAP_BUILDER_NAME]))


class BitbucketBuildStatusPush(BaseBuildStatusPush):
    """Send build result to bitbucket build status API."""
    name = "BitbucketBuildStatusPush"
    description_suffix = ''
    logger = Logger('eve.steps.BitbucketBuildStatusPush')
    BITBUCKET_STATUS_CORRESP = {
        SUCCESS: 'SUCCESSFUL',
        WARNINGS: 'SUCCESSFUL',
        FAILURE: 'FAILED',
        SKIPPED: 'FAILED',
        EXCEPTION: 'FAILED',
        CANCELLED: 'FAILED',
        RETRY: 'INPROGRESS',
        None: 'INPROGRESS'}

    def forge_url(self, build):
        """Forge the BB API URL on which the build status will be posted."""
        sha1 = build['buildset']['sourcestamps'][0]['revision']
        return 'https://api.bitbucket.org/2.0/repositories/' \
               '%(repo_owner)s/%(repo_name)s/commit/%(sha1)s/statuses/build' \
               % {
                   'repo_owner': 'scality',
                   'repo_name': self.repo,
                   'sha1': sha1
               }

    def add_tag(self, name, value, icon, color=None):
        name_value = '[%s: %s]' % (name, value)
        self.description_suffix = name_value + self.description_suffix

    @defer.inlineCallbacks
    def send(self, build):
        """Send build status to Bitbucket."""
        self.description_suffix = ''
        key, result, _, summary, description = self.gather_data(build)
        # Temporary hack to keep previous behaviour
        # Do not send status for other stagename than 'pre-merge' for now
        if key != 'pre-merge':
            return
        data = {
            'state': self.BITBUCKET_STATUS_CORRESP[result],
            'key': key,
            "name": summary,
            "url": build['url'],
            "description": description + self.description_suffix
        }
        url = self.forge_url(build)
        if 'eve.devsca.com' not in EXTERNAL_URL:
            self.logger.info("Bitbucket status not sent (not in prod) "
                             "(%s:%s on %s)" % (
                                 self.BITBUCKET_STATUS_CORRESP[result],
                                 key,
                                 url))
            return  # Don't really push status for tests
        http_service = yield HTTPClientService.getService(
            self.master, url, auth=(EVE_BITBUCKET_LOGIN, EVE_BITBUCKET_PWD))
        response = yield http_service.post('', json=data)
        # 200 means that the key already exists
        # 201 means that the key has been created successfully
        if response.code not in (200, 201):
            raise Exception(
                "{response.code}: unable to send status to Bitbucket: "
                "{url}\nRequest:\n{request}\nResponse:\n{response.content}".
                format(request=data, response=response, url=url))
        self.logger.info("Bitbucket status sent (%s:%s on %s)" % (
            self.BITBUCKET_STATUS_CORRESP[result],
            key,
            url))

