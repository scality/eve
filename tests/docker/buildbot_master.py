import os

from tests.util.buildbot_master import BuildbotMaster
from tests.util.cmd import cmd


class DockerizedBuildbotMaster(BuildbotMaster):
    _post_start_delay = 1
    _stop_cmd = 'docker rm -f {name}'

    def __init__(self, *args, **kwargs):
        """
        Dockerized buildbot master daemon

        Args:
            *args: Same as the BuildbotMaster class
            **kwargs: Same as the BuildbotMaster class
        """
        super(DockerizedBuildbotMaster, self).__init__(*args, **kwargs)
        self._env_file = os.path.join(self._base_path, 'docker.env')
        port = self.conf.pop('PB_PORT')
        self._start_cmd = [
            'docker', 'run',
            '--name', self._name,
            '-p', '{}:8999'.format(self.conf.pop('HTTP_PORT')),
            '-p',
            '{}:9999'.format(port), '-e', 'EXTERNAL_PB_PORT={}'.format(port),
            '-v', '/var/run/docker.sock:/var/run/docker.sock', '--env-file',
            self._env_file, 'eve_master'
        ]  # yapf: disable

    def pre_start_hook(self):
        """
        Builds an eve docker image and prepares the environment to run it.
        """
        cmd('docker build -t eve_master  .')
        self._env = self.environ
        self.dump(self._env_file)

    def _log(self):
        """
        Returns: the logs of the buildbot docker container
        """
        return cmd('docker logs {}'.format(self._name))
