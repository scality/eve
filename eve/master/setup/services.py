from os import environ

from buildbot.reporters.github import GitHubStatusPush

from reporters.base import BitbucketBuildStatusPush, HipChatBuildStatusPush


# pylint: disable=relative-import
def setup_reporters(project_name, bootstrap_builder_name, docker_builder_name,
                    openstack_builder_name):
    reporters = [HipChatBuildStatusPush(builders=[bootstrap_builder_name])]
    if 'github' in project_name:
        reporters.append(GitHubStatusPush(
            environ.pop('GITHUB_TOKEN'),
            builders=[bootstrap_builder_name]))
    else:
        reporters.append(BitbucketBuildStatusPush(
            builders=[docker_builder_name, openstack_builder_name]))
    return reporters
