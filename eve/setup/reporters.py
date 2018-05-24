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

from buildbot.plugins import reporters, util


def hipchat_reporter(builders_whitelist):
    assert util.env.HIPCHAT_ROOM
    assert util.env.HIPCHAT_TOKEN

    if util.env.HIPCHAT_REPORTER_STAGE_FILTER:
        stage_filter = util.env.HIPCHAT_REPORTER_STAGE_FILTER.split(';')
    else:
        stage_filter = []

    return reporters.HipChatBuildStatusPush(
        stage_filter,
        util.env.HIPCHAT_ROOM,
        util.env.HIPCHAT_TOKEN,
        builders=builders_whitelist
    )


def github_reporter(builders_whitelist):
    assert util.env.GITHUB_TOKEN

    if util.env.GIT_HOST_REPORTER_STAGE_FILTER:
        stage_filter = util.env.GIT_HOST_REPORTER_STAGE_FILTER.split(';')
    else:
        stage_filter = []

    return reporters.GithubBuildStatusPush(
        stage_filter,
        util.env.GITHUB_TOKEN,
        builders=builders_whitelist
    )


def bitbucket_reporter(builders_whitelist):
    assert util.env.EVE_GITHOST_LOGIN
    assert util.env.EVE_GITHOST_PWD

    if util.env.GIT_HOST_REPORTER_STAGE_FILTER:
        stage_filter = util.env.GIT_HOST_REPORTER_STAGE_FILTER.split(';')
    else:
        stage_filter = []

    return reporters.BitbucketBuildStatusPush(
        stage_filter,
        util.env.EVE_GITHOST_LOGIN,
        util.env.EVE_GITHOST_PWD,
        builders=builders_whitelist
    )


def ultron_reporter(builders_whitelist):
    assert util.env.ULTRON_REPORTER_URL

    if util.env.ULTRON_REPORTER_STAGE_FILTER:
        stage_filter = util.env.ULTRON_REPORTER_STAGE_FILTER.split(';')
    else:
        stage_filter = []

    return reporters.UltronBuildStatusPush(
        stage_filter,
        util.env.ULTRON_REPORTER_LOGIN,
        util.env.ULTRON_REPORTER_PWD,
        util.env.ULTRON_REPORTER_URL,
        builders=builders_whitelist
    )
