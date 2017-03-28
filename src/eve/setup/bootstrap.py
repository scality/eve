import netifaces
from buildbot.config import BuilderConfig
from buildbot.plugins import steps, util
from buildbot.process.factory import BuildFactory
from buildbot.process.properties import Interpolate, Property
from buildbot.process.results import SUCCESS
from buildbot.steps.master import SetProperty
from buildbot.steps.shell import SetPropertyFromCommand
from buildbot.steps.source.git import Git


def bootstrap_builder(workers):
    bootstrap_factory = BuildFactory()

    if util.env.RAX_LOGIN:
        bootstrap_factory.addStep(
            steps.CloudfilesAuthenticate(
                rax_login=util.env.RAX_LOGIN,
                rax_pwd=util.env.RAX_PWD))

    # EVE-361 adding git_config:
    # temporary workaround until we have bootstrap
    # running in a container linked to git_cache
    git_config = {
        'url.http://localhost:2222/bitbucket.org/.insteadOf':
            'git@bitbucket.org:',
        'url.http://localhost:2222/github.com/.insteadOf':
            'git@github.com:',
        'url.http://localhost:2222/mock/.insteadOf':
            'git@mock:'
    }
    bootstrap_factory.addStep(
        Git(name='checkout git branch',
            repourl=util.env.GIT_REPO,
            retry=(60, 10),
            submodules=True,
            branch=Property('branch'),
            mode='incremental',
            hideStepIf=lambda results, s: results == SUCCESS,
            haltOnFailure=True,
            config=git_config))

    bootstrap_factory.addStep(
        steps.CancelNonTipBuild())

    bootstrap_factory.addStep(
        SetProperty(
            name='setting the master_builddir property',
            property='master_builddir',
            hideStepIf=lambda results, s: results == SUCCESS,
            value=Property('builddir')))

    # Read conf from yaml file
    bootstrap_factory.addStep(steps.ReadConfFromYaml())

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

    bootstrap_factory.addStep(SetProperty(
        name='get the git host',
        property='git_host',
        hideStepIf=lambda results, s: results == SUCCESS,
        value=util.env.GIT_HOST))

    bootstrap_factory.addStep(SetProperty(
        name='get the git owner',
        property='git_owner',
        hideStepIf=lambda results, s: results == SUCCESS,
        value=util.env.GIT_OWNER))

    bootstrap_factory.addStep(SetProperty(
        name='get the repository name',
        property='git_slug',
        hideStepIf=lambda results, s: results == SUCCESS,
        value=util.env.GIT_SLUG))

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
        command=Interpolate('echo ' + util.env.ARTIFACTS_URL +
                            '/%(prop:artifacts_name)s'),
        hideStepIf=lambda results, s: results == SUCCESS,
        property='artifacts_public_url'))

    return BuilderConfig(
        name=util.env.BOOTSTRAP_BUILDER_NAME,
        workernames=[lw.name for lw in workers],
        factory=bootstrap_factory,
        properties={
            'artifacts_url': util.env.ARTIFACTS_URL,
            'artifacts_prefix': util.env.ARTIFACTS_PREFIX,
        },
    )
