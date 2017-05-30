"""Unit tests of `eve.steps.docker_build`."""

import unittest

import eve.steps.docker_build


class TestDockerBuild(unittest.TestCase):
    def test_init(self):
        ctx = eve.steps.docker_build.DockerBuild(
            'image', 'dockerfile', True, {'foo': 'bar'}, {'arg': 'val'})
        self.assertEquals(ctx.image, 'image')
        self.assertTrue(ctx.is_retry)
        self.assertFalse(ctx.isNewStyle())
        self.assertTrue(ctx == ctx)  # __eq__ coverage
        self.assertTrue(hash(ctx) == hash(ctx))  # __eq__ coverage
