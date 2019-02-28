"""Unit tests of `eve.steps.docker_build`."""

import unittest

import eve.steps.docker_build


class TestDockerBuild(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.docker_build.DockerBuild(
            'label', 'image', 'dockerfile', True,
            {'foo': 'bar'}, {'arg': 'val'})
        self.assertEquals(ctx.image, 'image')
        self.assertTrue(ctx.is_retry)
        self.assertFalse(ctx.isNewStyle())
        # [2019-03-01] David: Not sure what purpose is serving the following
        # test.
        self.assertTrue(ctx == ctx)  # __eq__ coverage


class TestDockerCheckLocalImage(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.docker_build.DockerCheckLocalImage(
            label='label', image='image', name='zippy')
        self.assertEquals(ctx.label, 'label')
        self.assertFalse(ctx.isNewStyle())
        self.assertEquals(ctx.name, 'zippy')


class DockerComputeImageFingerprint(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.docker_build.DockerComputeImageFingerprint(
            label='label', context_dir='/dummy', name='zippy')
        self.assertEquals(ctx.label, 'label')
        self.assertFalse(ctx.isNewStyle())
        self.assertEquals(ctx.name, 'zippy')


class TestDockerPull(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.docker_build.DockerPull(
            label='label', image='image', name='zippy')
        self.assertEquals(ctx.label, 'label')
        self.assertFalse(ctx.isNewStyle())
        self.assertEquals(ctx.name, 'zippy')


class TestDockerPush(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.docker_build.DockerBuild(
            label='label', image='image', name='zippy')
        self.assertEquals(ctx.name, 'zippy')
        self.assertEquals(ctx.image, 'image')
        # [2019-03-01] David: Not sure what purpose is serving the following
        # test.
        self.assertTrue(ctx == ctx)  # __eq__ coverage
