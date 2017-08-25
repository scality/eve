import argparse
import re
import socket
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader


def command_factory(cmd):
    """Return a command instance selected by input command."""

    try:
        return COMMANDS[cmd]()
    except IndexError:
        raise Exception("{} is not available.".format(cmd))


class BaseCommand():
    """Implement the command interface."""

    kube = False
    command = None
    template = None
    template_name = None
    kube_cmd_base = None
    namespace = None
    resource = None

    def __init__(self):
        if self.kube:
            env = Environment(
                loader=FileSystemLoader('/templates'),
                trim_blocks=True,
                lstrip_blocks=True
            )
        if self.template_name:
            self.template = env.get_template(self.template_name)

    def convert(self, cmd_str):
        original_cmd = cmd_str.split()
        if self.kube:
            self._parse(original_cmd)
            self.adapt_args()
            target_cmd = self._to_kube()
        else:
            target_cmd = original_cmd
        return target_cmd

    def _parse(self, docker_cmd):
        """Parse docker command line and return a namespace."""
        docker_cmd.remove(self.command)
        parser = argparse.ArgumentParser(prog='docker %s' % self.command,
                                         description='docker cli parser')
        self.register_args(parser)
        self.namespace = parser.parse_known_args(docker_cmd[1:])[0]

    def _to_kube(self):
        """Return a kube command line built from docker args."""
        if self.template:
            self.template.stream(vars(self.namespace)).dump(self.resource)
        if self.kube_cmd_base:
            # update resource in cmd line
            return [
                self.resource if it == '%resource%'
                else it for it in self.kube_cmd_base
            ]
        else:
            return ['true']  # shell noop

    def register_args(self, parser):
        """Register command specific args."""
        raise NotImplementedError()

    def adapt_args(self):
        """Adapt argument formatting from docker style to kube style."""
        raise NotImplementedError()


class Kill(BaseCommand):
    kube = True
    command = 'kill'
    template_name = None
    kube_cmd_base = ['kubectl', 'delete', 'job', '--output=name', '%resource%']

    def register_args(self, parser):
        parser.add_argument('container', action='store')

    def adapt_args(self):
        self.resource = self.namespace.container


class Pull(BaseCommand):
    kube = False
    command = 'pull'


class Push(BaseCommand):
    kube = False
    command = 'push'


class Rm(BaseCommand):
    kube = True
    command = 'rm'
    template_name = None
    kube_cmd_base = ['rm', '-f', '%resource%']

    def register_args(self, parser):
        parser.add_argument('container', action='store')

    def adapt_args(self):
        self.resource = '/resource/' + self.namespace.container


class Run(BaseCommand):
    kube = True
    command = 'run'
    template_name = 'worker_run.yml'
    kube_cmd_base = ['kubectl', 'create', '--no-headers',
                     '--output=custom-columns=NAME:.metadata.name',
                     '-f', '%resource%']

    def register_args(self, parser):
        def dictify_equal(arg):
            name, value = arg.split('=')
            return {'name': name, 'value': value}

        def dictify_port(arg):
            values = arg.split(':')
            if len(values) == 1:
                return {
                    'value': values[0],
                    'target': values[0],
                    'name': 'port-' + str(uuid4())[:13]
                }
            elif len(values) == 2:
                return {
                    'value': values[0],
                    'target': values[1],
                    'name': 'port-' + str(uuid4())[:13]}
            raise Exception('unsupported port type')

        def dictify_volume(arg):
            values = arg.split(':')
            if len(values) == 1:
                return {
                    'name': 'volume-' + str(uuid4())[:13],
                    'mountpath': values[0],
                    'readonly': False
                }
            # ignore unsupported volume specification
            return None

        # unique random name (name is mandatory for kube)
        default_name = '%s-worker-%s' % (
            socket.gethostname(),
            str(uuid4())[:8]
        )
        parser.add_argument('--privileged', action='store_true')
        parser.add_argument('-e', '--env', action='append',
                            default=[], type=dictify_equal)
        parser.add_argument('-l', '--label', action='append',
                            default=[], type=dictify_equal)
        parser.add_argument('--name', action='store',
                            default=default_name)
        parser.add_argument('-p', '--publish', action='append',
                            default=[], type=dictify_port)
        parser.add_argument('-v', '--volume', action='append',
                            default=[], type=dictify_volume)
        parser.add_argument('image', action='store')

    def adapt_args(self):
        self.resource = '/resource/' + self.namespace.name
        vars(self.namespace)['docker_hook_sidecar'] = False

        for label in self.namespace.label:
            if label['name'] == 'docker_in_docker':
                vars(self.namespace)['docker_hook_sidecar'] = True
                vars(self.namespace)['docker_hook_image'] = re.sub(
                    r'([^/]*/[^/]*/)[^:]*:.*',
                    r'\1docker-hook:%s' % label['value'],
                    self.namespace.image
                )
                break


class Wait(BaseCommand):
    kube = True
    command = 'wait'
    template_name = None
    kube_cmd_base = None

    def register_args(self, parser):
        pass

    def adapt_args(self):
        pass


COMMANDS = {
    'kill': Kill,
    'pull': Pull,
    'push': Push,
    'rm': Rm,
    'run': Run,
    'wait': Wait,
}
