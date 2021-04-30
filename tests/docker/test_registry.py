import unittest

from tests.docker.registry import DockerizedRegistry
from tests.util.cmd import cmd


class TestDockerizedRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = DockerizedRegistry()
        print('Registry URL: {}:{}'.format(self.registry.external_ip,
                                           self.registry.port))
        assert self.registry is self.registry.start()

    def tearDown(self):
        self.registry.stop()

    def test_start_stop(self):
        cmd('docker pull ubuntu:bionic')
        name = '{}:{}/test_registry_start_stop'.format(
            self.registry.external_ip, self.registry.port)
        cmd('docker tag ubuntu:bionic {}'.format(name))
        cmd('docker push {}'.format(name))
        assert name in cmd('docker images')
        cmd('docker rmi {}'.format(name))
        assert name not in cmd('docker images')
        cmd('docker pull {}'.format(name))
        assert name in cmd('docker images')
