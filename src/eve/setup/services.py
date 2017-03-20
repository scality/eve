from os import environ

from buildbot.plugins import reporters
from buildbot.reporters.github import GitHubStatusPush


# pylint: disable=relative-import
def setup_reporters(project_name, bootstrap_builder_name,
                    docker_builder_name,
                    openstack_builder_name):
    reports = [
        reporters.HipChatBuildStatusPush(builders=[bootstrap_builder_name])]
    if 'github' in project_name:
        reports.append(GitHubStatusPush(
            environ.pop('GITHUB_TOKEN'),
            builders=[bootstrap_builder_name]))
    else:
        reports.append(reporters.BitbucketBuildStatusPush(
            builders=[docker_builder_name, openstack_builder_name]))
    return reports
