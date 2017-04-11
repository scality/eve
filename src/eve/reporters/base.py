"""Allow eve to send reports."""
import re

from buildbot.process.results import (CANCELLED, EXCEPTION, FAILURE, RETRY,
                                      SKIPPED, SUCCESS, WARNINGS, Results)
from buildbot.reporters import utils
from buildbot.reporters.github import GitHubStatusPush
from buildbot.reporters.http import HttpStatusPushBase
from buildbot.util.httpclientservice import HTTPClientService
from twisted.internet import defer
from twisted.logger import Logger

REPO_ICON = 'http://www.packal.org/sites/default/files/public/styles/icon_' \
            'large/public/workflow-files/netdeanishealfred-git-repos/icon/' \
            'icon.png?itok=1zkuMgPa'
BRANCH_ICON = 'http://plainicon.com/dboard/userprod/2800_a1826/prod_thumb/' \
              'plainicon.com-50219-512px-201.png'
CLOCK_ICON = 'https://image.freepik.com/free-icon/clock-of-circular-shape-at' \
             '-two-o-clock_318-48022.jpg'


class BaseBuildStatusPush(HttpStatusPushBase):
    """
    Base class for pushing build status
    """
    repo = None
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
    def getDetailsForTriggeredBuilds(self, build):  # noqa
        """get details for triggered builds."""
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
        """
        Gathers data to be used in build status
        :param build: The build dictionary
        :return: (key, result, title, summary, description)
        """
        key = build['properties']['stage_name'][0]
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

    def getStepsWithResult(self, build):  # noqa
        """get steps with result."""
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
                        res.append('%s -> %s' % (stage_name,
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


class BuildStatusPushMixin(object):
    # pylint: disable=too-few-public-methods
    def _filterBuilds(self, filter_build, build):
        try:
            key = build['properties']['stage_name'][0]
        except (KeyError, IndexError):
            self.logger.error('no valid stage_name property found')
        else:
            if key not in ['pre-merge', 'post-merge']:
                return False
        return filter_build(build)


class HipChatBuildStatusPush(BaseBuildStatusPush, BuildStatusPushMixin):
    """Send build result to HipChat build status API."""
    name = 'HipChatBuildStatusPush'
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

    def __init__(self, room_id, token, **kwargs):
        self.room_id = room_id
        self.token = token
        super(HipChatBuildStatusPush, self).__init__(**kwargs)

    def add_tag(self, name, value, icon, color=None):
        attr = dict(label=name, value=dict(label=value))
        if color in self.COLOR_STYLE_CORRESP:
            attr['value']['style'] = self.COLOR_STYLE_CORRESP[color]
        if icon:
            attr['value']['icon'] = dict(url=icon)
        self.attributes.append(attr)

    def filterBuilds(self, build):
        return self._filterBuilds(
            super(HipChatBuildStatusPush, self).filterBuilds,
            build)

    @defer.inlineCallbacks
    def send(self, build):
        """Send build status to HipChat."""
        if not self.room_id or not self.token:
            self.logger.info(
                'Hipchat status not sent'
                ' (HIPCHAT_* variables not defined))'
            )
            return

        self.attributes = []
        key, result, title, summary, description = self.gather_data(build)

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

        url = 'https://api.hipchat.com/v2/room/%s/notification' % self.room_id

        http_service = yield HTTPClientService.getService(self.master, url)
        response = yield http_service.post('', json=data, params={
            'auth_token': self.token
        })

        if response.code != 204:
            raise Exception(
                "{response.code}: unable to send status to HipChat: "
                "{url}\nRequest:\n{request}\nResponse:\n{response.content}".
                format(request=data, response=response, url=url))

        self.logger.info('HipChat status sent')


class BitbucketBuildStatusPush(BaseBuildStatusPush, BuildStatusPushMixin):
    """Send build result to bitbucket build status API."""
    name = 'BitbucketBuildStatusPush'
    description_suffix = ''
    logger = Logger('eve.steps.BitbucketBuildStatusPush')
    BITBUCKET_STATUS_CORRESP = {
        SUCCESS: 'SUCCESSFUL',
        WARNINGS: 'SUCCESSFUL',
        FAILURE: 'FAILED',
        SKIPPED: 'STOPPED',
        EXCEPTION: 'FAILED',
        CANCELLED: 'STOPPED',
        RETRY: 'INPROGRESS',
        None: 'INPROGRESS',
    }

    def __init__(self, login, password, **kwargs):
        self.login = login
        self.password = password
        super(BitbucketBuildStatusPush, self).__init__(**kwargs)

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

    def filterBuilds(self, build):
        return self._filterBuilds(
            super(BitbucketBuildStatusPush, self).filterBuilds,
            build)

    @defer.inlineCallbacks
    def send(self, build):
        """Send build status to Bitbucket."""
        self.description_suffix = ''
        key, result, _, summary, description = self.gather_data(build)
        # Temporary hack to keep previous behaviour
        # Do not send status for other stages than 'pre-merge' or 'post-merge'
        data = {
            'state': self.BITBUCKET_STATUS_CORRESP[result],
            'key': key,
            'name': summary,
            'url': build['url'],
            'description': description + self.description_suffix
        }
        url = self.forge_url(build)

        http_service = yield HTTPClientService.getService(
            self.master, url, auth=(self.login, self.password))
        response = yield http_service.post('', json=data)
        # 200 means that the key already exists
        # 201 means that the key has been created successfully
        if response.code not in (200, 201):
            raise Exception(
                "{response.code}: unable to send status to Bitbucket: "
                "{url}\nRequest:\n{request}\nResponse:\n{response.content}".
                format(request=data, response=response, url=url))
        self.logger.info('Bitbucket status sent (%s:%s on %s)' % (
            self.BITBUCKET_STATUS_CORRESP[result],
            key,
            url))


class GithubBuildStatusPush(GitHubStatusPush, BuildStatusPushMixin):
    """Send build result to github build status API."""
    logger = Logger('eve.steps.GithubBuildStatusPush')

    def filterBuilds(self, build):
        return self._filterBuilds(
            super(GithubBuildStatusPush, self).filterBuilds,
            build)

    @defer.inlineCallbacks
    def send(self, build):
        key = build['properties']['stage_name'][0]
        self.context = key  # pylint: disable=attribute-defined-outside-init
        return super(GithubBuildStatusPush, self).send(build)
