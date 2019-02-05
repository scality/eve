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


def github_reporter():
    assert util.env.GITHUB_TOKEN

    return reporters.GithubBuildStatusPush(
        util.env.GITHUB_TOKEN,
    )


def bitbucket_reporter():
    assert util.env.EVE_GITHOST_LOGIN
    assert util.env.EVE_GITHOST_PWD

    return reporters.BitbucketBuildStatusPush(
        util.env.EVE_GITHOST_LOGIN,
        util.env.EVE_GITHOST_PWD,
    )


def ultron_reporter():
    assert util.env.ULTRON_REPORTER_URL

    return reporters.UltronBuildStatusPush(
        util.env.ULTRON_REPORTER_LOGIN,
        util.env.ULTRON_REPORTER_PWD,
        util.env.ULTRON_REPORTER_URL,
    )
