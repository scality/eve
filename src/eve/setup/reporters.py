from buildbot.plugins import reporters, util


def hipchat_reporter():
    assert util.env.HIPCHAT_ROOM
    assert util.env.HIPCHAT_TOKEN

    builders = [
        util.env.DOCKER_BUILDER_NAME,
        util.env.OPENSTACK_BUILDER_NAME
    ]

    return reporters.HipChatBuildStatusPush(
        util.env.HIPCHAT_ROOM,
        util.env.HIPCHAT_TOKEN,
        builders=builders
    )


def github_reporter():
    assert util.env.GITHUB_TOKEN

    builders = [
        util.env.DOCKER_BUILDER_NAME,
        util.env.OPENSTACK_BUILDER_NAME
    ]

    return reporters.GithubBuildStatusPush(
        util.env.GITHUB_TOKEN,
        builders=builders
    )


def bitbucket_reporter():
    assert util.env.EVE_GITHOST_LOGIN
    assert util.env.EVE_GITHOST_PWD

    builders = [
        util.env.DOCKER_BUILDER_NAME,
        util.env.OPENSTACK_BUILDER_NAME
    ]

    return reporters.BitbucketBuildStatusPush(
        util.env.EVE_GITHOST_LOGIN,
        util.env.EVE_GITHOST_PWD,
        builders=builders
    )
