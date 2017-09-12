import argparse
import os
import re
import socket
import tarfile
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader


def command_factory(cmd):
    """Return a command instance selected by input command."""

    try:
        return COMMANDS[cmd]()
    except KeyError:
        return Docker()


class BaseCommand():
    """Implement the command interface."""

    command = None
    template = None
    template_name = None
    new_command = None
    post_command = []
    namespace = None
    resource = None

    def __init__(self):
        env = Environment(
            loader=FileSystemLoader('/templates'),
            trim_blocks=True,
            lstrip_blocks=True
        )
        if self.template_name:
            self.template = env.get_template(self.template_name)

    def convert(self, original_cmd, files=None):
        """Convert original docker command to new command.

        - parse original command line and return a namespace,
        - adapt args,
        - build and return the new command line.

        """
        original_cmd.remove(self.command)
        parser = argparse.ArgumentParser(prog='docker %s' % self.command,
                                         description='docker cli parser')
        self.register_args(parser)
        self.namespace = parser.parse_known_args(original_cmd[1:])[0]

        self.adapt_args(files)

        if self.template:
            self.template.stream(vars(self.namespace)).dump(self.resource)
        # update resource in cmd line
        return ([self.resource if it == '%resource%'
                 else it for it in self.new_command],
                [self.resource if it == '%resource%'
                 else it for it in self.post_command])

    def register_args(self, parser):
        """Register command specific args."""
        raise NotImplementedError()

    def adapt_args(self, files):
        """Adapt argument formatting from docker style to kube style."""
        raise NotImplementedError()


class Build(BaseCommand):
    command = 'build'
    new_command = ['docker', 'build', '%resource%']
    post_command = ['rm', '-rf', '%resource%']

    def register_args(self, parser):
        def dictify_equal(arg):
            name, value = arg.split('=')
            return {'name': name, 'value': value}

        parser.add_argument('path')
        parser.add_argument('--rm', action='store_true')
        parser.add_argument('--quiet', action='store_true')
        parser.add_argument('--build-arg', action='append', default=[])
        parser.add_argument('--tag', '-t', action='append', default=[])
        parser.add_argument('-l', '--label', action='append',
                            default=[], type=dictify_equal)

    def adapt_args(self, files):
        docker_context_archive = files['docker_context']
        archive_name = docker_context_archive.filename
        archive_path = os.path.join('/resource', archive_name)
        new_path = os.path.join(
            '/resource', re.sub('\.tar.gz$', '', archive_name))
        docker_context_archive.save(archive_path)
        tar = tarfile.open(archive_path, "r:gz")
        tar.extractall(path=new_path)
        tar.close()
        os.remove(archive_path)
        self.resource = new_path

        self.new_command = list(self.new_command)
        if self.namespace.rm:
            self.new_command.insert(2, '--rm')

        if self.namespace.quiet:
            self.new_command.insert(2, '--quiet')

        for arg in self.namespace.build_arg:
            self.new_command.insert(2, '--build-arg')
            self.new_command.insert(3, arg)

        for tag in self.namespace.tag:
            self.new_command.insert(2, '--tag')
            self.new_command.insert(3, tag)


class Kill(BaseCommand):
    command = 'kill'
    new_command = ['kubectl', 'delete', 'job', '--output=name', '%resource%']

    def register_args(self, parser):
        parser.add_argument('container')

    def adapt_args(self, files):
        self.resource = self.namespace.container


class Rm(BaseCommand):
    command = 'rm'
    new_command = ['rm', '-f', '%resource%']

    def register_args(self, parser):
        parser.add_argument('container')

    def adapt_args(self, files):
        self.resource = '/resource/' + self.namespace.container


class Run(BaseCommand):
    command = 'run'
    template_name = 'worker_run.yml'
    new_command = ['kubectl', 'create', '--no-headers',
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
        parser.add_argument('--name',
                            default=default_name)
        parser.add_argument('-p', '--publish', action='append',
                            default=[], type=dictify_port)
        parser.add_argument('-v', '--volume', action='append',
                            default=[], type=dictify_volume)
        parser.add_argument('image')

    def adapt_args(self, files):
        self.resource = '/resource/' + self.namespace.name
        vars(self.namespace)['docker_hook_sidecar'] = True
        vars(self.namespace)['docker_hook_image'] = re.sub(
            r'([^/]*/[^/]*/)[^:]*:.*',
            r'\1docker-hook:%s' % 'user_bertrand_odr_kube',
            self.namespace.image)


class Docker(BaseCommand):
    """Call docker with original command."""

    def convert(self, original_cmd, files=None):
        new_cmd = original_cmd
        new_cmd[0] = 'docker'
        return new_cmd, None


class Ignore(BaseCommand):
    """Simply ignore command."""

    def convert(self, original_cmd, files=None):
        return ['true'], None  # shell noop


COMMANDS = {
    'build': Build,
    'kill': Kill,
    'rm': Rm,
    'run': Run,
    'wait': Ignore,
}
