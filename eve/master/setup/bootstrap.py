from os import environ
from tempfile import mkdtemp

import netifaces
from buildbot.config import BuilderConfig
from buildbot.locks import MasterLock
from buildbot.process.factory import BuildFactory
from buildbot.process.properties import Interpolate, Property
from buildbot.process.results import SUCCESS
from buildbot.steps.master import SetProperty
from buildbot.steps.shell import SetPropertyFromCommand, ShellCommand
from buildbot.steps.source.git import Git

from steps.artifacts import CloudfilesAuthenticate
from steps.cancel import CancelNonTipBuild
from steps.yaml_parser import ReadConfFromYaml


def setup_bootstrap(git_repo, project_name,
                    bootstrap_builder_name, local_workers,
                    openstack_credentials,
                    artifacts_url, artifacts_prefix):
    local_git_repo = environ.pop('LOCAL_GIT_REPO')
    bootstrap_factory = BuildFactory()
    git_repo_short = git_repo.split('/')[-1].replace('.git', '')

    git_cache_dir_host = mkdtemp(prefix=git_repo_short)
    if openstack_credentials['login']:
        bootstrap_factory.addStep(
            CloudfilesAuthenticate(rax_login=openstack_credentials['login'],
                                   rax_pwd=openstack_credentials['password']))

    # Check out the source
    git_cache_update_lock = MasterLock('git_cache_update')
    bootstrap_factory.addStep(
        ShellCommand(name='update git repo cache',
                     workdir=git_cache_dir_host,
                     command=(
                         'git clone --mirror --recursive %s . || '
                         'git remote update' % local_git_repo),
                     locks=[git_cache_update_lock.access('exclusive')],
                     hideStepIf=lambda results, s: results == SUCCESS,
                     haltOnFailure=True))

    bootstrap_factory.addStep(CancelNonTipBuild(workdir=git_cache_dir_host))

    bootstrap_factory.addStep(
        SetPropertyFromCommand(
            name='get the git sha1 from the branch name',
            command=Interpolate('cd ' + git_cache_dir_host +
                                ' && git rev-list -1 %(prop:branch)s'),
            hideStepIf=lambda results, s: results == SUCCESS,
            property='revision'))

    bootstrap_factory.addStep(
        SetProperty(
            name='setting the master_builddir property',
            property='master_builddir',
            hideStepIf=lambda results, s: results == SUCCESS,
            value=Property('builddir')))

    bootstrap_factory.addStep(
        Git(name='checkout git branch',
            repourl=git_cache_dir_host,
            shallow=True,
            retry=(60, 10),
            submodules=True,
            mode='incremental',
            hideStepIf=lambda results, s: results == SUCCESS,
            haltOnFailure=True))
    # Read conf from yaml file
    bootstrap_factory.addStep(ReadConfFromYaml())

    docker_host_ip = '127.0.0.1'  # Dummy default value
    try:
        docker_addresses = netifaces.ifaddresses('docker0')
    except ValueError:
        pass
    else:
        try:
            docker_host_ip = (docker_addresses[netifaces.AF_INET]
                              [0]['addr'])
        except KeyError:
            pass
    git_host, git_owner, git_slug = project_name.split('_', 2)

    bootstrap_factory.addStep(SetProperty(
        name='get the git host',
        property='git_host',
        hideStepIf=lambda results, s: results == SUCCESS,
        value=git_host))
    bootstrap_factory.addStep(SetProperty(
        name='get the git owner',
        property='git_owner',
        hideStepIf=lambda results, s: results == SUCCESS,
        value=git_owner))
    bootstrap_factory.addStep(SetProperty(
        name='get the repository name',
        property='git_slug',
        hideStepIf=lambda results, s: results == SUCCESS,
        value=git_slug))
    bootstrap_factory.addStep(SetPropertyFromCommand(
        name='get the product version',
        command=('./eve/get_product_version.sh 2> /dev/null'
                 ' || echo 0.0.0'),
        hideStepIf=lambda results, s: results == SUCCESS,
        property='product_version'))
    bootstrap_factory.addStep(SetPropertyFromCommand(
        name='set the artifacts base name',
        command=Interpolate('echo %(prop:git_host)s'
                            ':%(prop:git_owner)s'
                            ':%(prop:git_slug)s'
                            ':%(prop:artifacts_prefix)s'
                            '%(prop:product_version)s'
                            '.r%(prop:commit_timestamp)s'
                            '.%(prop:commit_short_revision)s'),
        hideStepIf=lambda results, s: results == SUCCESS,
        property='artifacts_base_name'))
    bootstrap_factory.addStep(SetPropertyFromCommand(
        name='set the artifacts name',
        command=Interpolate('echo %(prop:artifacts_base_name)s'
                            '.%(prop:pipeline)s'
                            '.%(prop:b4nb)s'),
        hideStepIf=lambda results, s: results == SUCCESS,
        property='artifacts_name'))
    bootstrap_factory.addStep(SetProperty(
        name='set the artifacts local reverse proxy',
        property='artifacts_local_reverse_proxy',
        hideStepIf=lambda results, s: results == SUCCESS,
        value='http://' + docker_host_ip + ':1080/'))
    bootstrap_factory.addStep(SetPropertyFromCommand(
        name='set the artifacts private url',
        command=Interpolate('echo http://' + docker_host_ip +
                            ':1080/builds/'
                            '%(prop:artifacts_name)s'),
        hideStepIf=lambda results, s: results == SUCCESS,
        property='artifacts_private_url'))
    bootstrap_factory.addStep(SetPropertyFromCommand(
        name='set the artifacts public url',
        command=Interpolate('echo ' + artifacts_url +
                            '/%(prop:artifacts_name)s'),
        hideStepIf=lambda results, s: results == SUCCESS,
        property='artifacts_public_url'))

    return BuilderConfig(
        name=bootstrap_builder_name,
        workernames=[lw.name for lw in local_workers],
        factory=bootstrap_factory,
        properties={
            'artifacts_url': artifacts_url,
            'artifacts_prefix': artifacts_prefix,
        },
    )
