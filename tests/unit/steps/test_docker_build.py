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
        self.assertTrue(ctx == ctx)  # __eq__ coverage
        self.assertTrue(hash(ctx) == hash(ctx))  # __eq__ coverage


class TestDockerCheckLocalImage(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.docker_build.DockerCheckLocalImage(
            label='label', image='image', name='zippy')
        self.assertEquals(ctx.label, 'label')
        self.assertEquals(ctx.name, 'zippy')

    def test_extract_fn(self):
        ctx = eve.steps.docker_build.DockerCheckLocalImage(
            label='label', image='image')
        self.assertEquals(
            ctx.extract_fn(0, 'stdout', 'stderr'),
            {'exists_label': True})
        self.assertEquals(
            ctx.extract_fn(1, 'stdout', 'stderr'),
            {'exists_label': False})
        self.assertEquals(
            ctx.extract_fn(127, 'stdout', 'stderr'),
            {'exists_label': False})


class DockerComputeImageFingerprint(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.docker_build.DockerComputeImageFingerprint(
            label='label', context_dir='/dummy', name='zippy')
        self.assertEquals(ctx.property, 'fingerprint_label')
        self.assertEquals(ctx.name, 'zippy')


class TestDockerPull(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.docker_build.DockerPull(
            label='label', image='image', name='zippy')
        self.assertEquals(ctx.label, 'label')
        self.assertEquals(ctx.name, 'zippy')

    def test_extract_fn(self):
        ctx = eve.steps.docker_build.DockerPull(
            label='label', image='image')
        self.assertEquals(
            ctx.extract_fn(0, 'stdout', 'stderr'),
            {'exists_label': True})
        self.assertEquals(
            ctx.extract_fn(1, 'stdout', 'stderr'),
            {'exists_label': False})
        self.assertEquals(
            ctx.extract_fn(127, 'stdout', 'stderr'),
            {'exists_label': False})


class TestDockerPush(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.docker_build.DockerBuild(
            label='label', image='image', name='zippy')
        self.assertEquals(ctx.name, 'zippy')
        self.assertEquals(ctx.image, 'image')
        self.assertTrue(ctx == ctx)  # __eq__ coverage
        self.assertTrue(hash(ctx) == hash(ctx))  # __eq__ coverage