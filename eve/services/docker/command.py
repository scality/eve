import argparse
import os
import re
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader


def command_factory(cmd):
    """Return a BaseCommand instance selected by input operation."""

    try:
        return OPERATIONS[cmd]()
    except KeyError:
        return Docker()


class Argparse(argparse.ArgumentParser):
    def error(self, msg):
        raise Exception(msg)


class BaseCommand():
    """Implement the command interface."""

    operation = None
    template = None

    def convert(self, original_cmd, stdin, files=None):
        """Convert original docker command to new command.

        - parse original command line and return a namespace,
        - adapt args,
        - build and return the new command line.

        """
        cmd = list(original_cmd)
        cmd.remove(self.operation)
        parser = Argparse(prog='docker %s' % self.operation,
                          description='docker cli parser')
        self.register_args(parser)
        try:
            namespace = parser.parse_known_args(cmd[1:])[0]
        except Exception:
            return Docker().convert(original_cmd, stdin, files)

        args = self.adapt_args(namespace, stdin, files) or []

        if self.template:
            env = Environment(
                loader=FileSystemLoader('/templates'),
                trim_blocks=True,
                lstrip_blocks=True
            )
            template = env.get_template(self.template)
            template.stream(vars(namespace)) \
                    .dump('/resource/' + self.get_template_basename(namespace))

        return ['/commands/' + self.operation] + args

    def register_args(self, parser):
        """Register docker command specific args."""
        pass

    def adapt_args(self, namespace, stdin, files):
        """Post process given arguments and return new args."""
        pass

    def get_new_args(self, namespace, files):
        return []

    def get_template_basename(self, namespace):
        """Return basename of rendered template."""
        raise NotImplementedError()


class Build(BaseCommand):
    operation = 'build'

    def register_args(self, parser):
        def dictify_equal(arg):
            name, value = arg.split('=')
            return {'name': name, 'value': value}

        parser.add_argument('path')
        parser.add_argument('--rm', action='store_true')
        parser.add_argument('--quiet', '-q', action='store_true')
        parser.add_argument('--build-arg', action='append', default=[])
        parser.add_argument('--tag', '-t', action='append', default=[])
        parser.add_argument('--label', '-l', action='append',
                            default=[], type=dictify_equal)

    def adapt_args(self, namespace, stdin, files):
        docker_context_archive = files['docker_context']
        archive_name = docker_context_archive.filename
        archive_path = os.path.join('/resource', archive_name)
        docker_context_archive.save(archive_path)

        build_cmd = ['docker', 'build']
        if namespace.rm:
            build_cmd.append('--rm')

        if namespace.quiet:
            build_cmd.append('--quiet')

        for arg in namespace.build_arg:
            build_cmd.append('--build-arg')
            build_cmd.append(arg)

        tag = ''
        for arg in namespace.tag:
            build_cmd.append('--tag')
            build_cmd.append(arg)
            tag = arg

        for arg in namespace.label:
            build_cmd.append('--label')
            build_cmd.append('%s=%s' % (arg['name'], arg['value']))

        return [
            archive_path,
            os.environ['REGISTRY'],
            tag,
            ' '.join(build_cmd)
        ]


class Docker(BaseCommand):
    """Call docker with original command."""

    def convert(self, original_cmd, stdin, files=None):
        new_cmd = list(original_cmd)
        new_cmd[0] = 'docker'
        return new_cmd


class Exec(BaseCommand):
    operation = 'exec'

    def register_args(self, parser):
        parser.add_argument('--interactive', '-i', action='store_true')
        parser.add_argument('--tty', '-t', action='store_true')
        parser.add_argument('container')
        parser.add_argument('command')
        parser.add_argument('args', nargs=argparse.REMAINDER)

    def adapt_args(self, namespace, stdin, files):
        args = []
        options = []

        if namespace.interactive:
            options.append('-i')

        if namespace.tty:
            options.append('-t')

        args.append(' '.join(options))
        args.append(namespace.container)
        args.append(namespace.command)
        args.append(' '.join(namespace.args))
        if stdin:
            args.append('\n'.join(stdin))
        return args


class Ignore(BaseCommand):
    """Simply ignore command."""

    def convert(self, original_cmd, stdin, files=None):
        return ['true']  # shell noop


class Inspect(BaseCommand):
    operation = 'inspect'

    def register_args(self, parser):
        parser.add_argument('container')
        parser.add_argument('--format', default='')

    def adapt_args(self, namespace, stdin, files):
        return [namespace.format, namespace.container]


class Kill(BaseCommand):
    operation = 'kill'

    def register_args(self, parser):
        parser.add_argument('container')

    def adapt_args(self, namespace, stdin, files):
        return [namespace.container]


class Ps(BaseCommand):
    operation = 'ps'

    def register_args(self, parser):
        def dictify_equal(arg):
            try:
                filter_, name, value = arg.split('=')
            except ValueError:
                filter_, value = arg.split('=')
                name = None
            return {'filter': filter_, 'name': name, 'value': value}

        parser.add_argument('--filter', '-f', action='append',
                            default=[], type=dictify_equal)
        parser.add_argument('--all', '-a', action='store_true')

    def adapt_args(self, namespace, stdin, files):
        args = []

        if namespace.all:
            args.append('--show-all')

        filters = []
        for filter_ in namespace.filter:
            if filter_['filter'] == 'label':
                filters.append('--selector')
                filters.append('%s=%s' % (filter_['name'], filter_['value']))
            elif filter_['filter'] == 'status':
                # deliberatly choose to ignore filter for now
                pass
            elif filter_['filter'] == 'id':
                # id is not compatible with selectors
                args.append(filter_['value'].replace('___', '-'))
                filters = []
                break
            else:
                raise NotImplementedError()
        args.extend(filters)

        return args


class Run(BaseCommand):
    operation = 'run'
    template = 'worker_run.yml'

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
                    'type': 'emptyDir',
                    'name': 'volume-' + str(uuid4())[:13],
                    'mountpath': values[0],
                    'readonly': False
                }
            elif len(values) == 2:
                return {
                    'type': 'hostPath',
                    'name': 'volume-' + str(uuid4())[:13],
                    'hostpath': values[0],
                    'mountpath': values[1],
                    'readonly': False
                }
            elif len(values) == 3:
                return {
                    'type': 'hostPath',
                    'name': 'volume-' + str(uuid4())[:13],
                    'hostpath': values[0],
                    'mountpath': values[1],
                    'readonly': True if values[2] == 'ro' else False
                }
            return None

        parser.add_argument('--cpu-quota')
        parser.add_argument('--cpu-period')
        parser.add_argument('--memory')
        parser.add_argument('--memory-swap')
        parser.add_argument('--detach', action='store_true')
        parser.add_argument('--privileged', action='store_true')
        parser.add_argument('--stop-signal')
        parser.add_argument('-e', '--env', action='append',
                            default=[], type=dictify_equal)
        parser.add_argument('-l', '--label', action='append',
                            default=[], type=dictify_equal)
        parser.add_argument('--name')
        parser.add_argument('-p', '--publish', action='append',
                            default=[], type=dictify_port)
        parser.add_argument('-v', '--volume', action='append',
                            default=[], type=dictify_volume)
        parser.add_argument('image')

    def adapt_args(self, namespace, stdin, files):
        vars(namespace)['docker_hook_sidecar'] = False
        vars(namespace)['buildnumber'] = os.environ.get('BUILDNUMBER', '0')

        if namespace.image.startswith('sha256:'):
            vars(namespace)['image'] = \
                namespace.image.replace(
                    'sha256:',
                    os.environ['REGISTRY'] + '/unspecified:')

        for label in namespace.label:
            if label['name'] == 'docker_hook':
                vars(namespace)['docker_hook_sidecar'] = True
                vars(namespace)['registry'] = os.environ['REGISTRY']
                vars(namespace)['docker_hook_image'] = re.sub(
                    r'([^/]*/[^/]*/)[^:]*:.*',
                    r'\1docker-hook:%s' % label['value'],
                    namespace.image
                )
                break
            if label['name'] == 'buildnumber':
                vars(namespace)['buildnumber'] = label['value']

        if namespace.docker_hook_sidecar:
            # ensure we don't attach doker volumes twice
            for index, volume in enumerate(namespace.volume):
                if (volume
                    and 'hostpath' in volume
                    and volume['hostpath'] in [
                        '/var/run/docker.sock', '/var/lib/docker']):
                    vars(namespace)['volume'][index] = None

        vars(namespace)['cpu_limit'] = os.environ.get(
            'WORKER_CPU_LIMIT', '1')
        vars(namespace)['memory_limit'] = os.environ.get(
            'WORKER_MEMORY_LIMIT', '1Gi')
        vars(namespace)['cpu_request'] = os.environ.get(
            'WORKER_CPU_REQUEST', '100m')
        vars(namespace)['memory_request'] = os.environ.get(
            'WORKER_MEMORY_REQUEST', '1Gi')

        vars(namespace)['namespace'] = os.environ.get(
            'NAMESPACE', 'unknown')

        # unique random name
        if namespace.name is None:
            vars(namespace)['name'] = 'worker-%s-%s' % (
                namespace.buildnumber,
                str(uuid4())[:5]
            )

        return [namespace.name]

    def get_template_basename(self, namespace):
        return namespace.name


class Rm(BaseCommand):
    operation = 'rm'

    def register_args(self, parser):
        parser.add_argument('container')

    def adapt_args(self, namespace, stdin, files):
        return [namespace.container]


class Stop(BaseCommand):
    operation = 'stop'

    def register_args(self, parser):
        parser.add_argument('--time', '-t', default='10')
        parser.add_argument('container')

    def adapt_args(self, namespace, stdin, files):
        return [
            namespace.container,
            namespace.time
        ]


OPERATIONS = {
    'build': Build,
    'exec': Exec,
    'inspect': Inspect,
    'kill': Kill,
    'ps': Ps,
    'rm': Rm,
    'run': Run,
    'stop': Stop,
    'wait': Ignore,
}
