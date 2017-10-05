"""Unit tests of `eve.steps.patcher`."""

from __future__ import absolute_import

from twisted.trial import unittest

from eve.steps.patcher import Patcher


class TestPatcher(unittest.TestCase):
    test_step_1 = {}
    test_step_2 = {'name': 'test step'}
    test_step_3 = {'name': 'dummy other step name'}
    test_step_4 = {'name': 'test step 4',
                   'doStepIf': True,
                   'descriptionDone': 'done'}

    def test_empty_config(self):
        config = {}
        patcher = Patcher(config)
        self.assertFalse(patcher.is_branch_skipped('a_branch'))
        self.assertEqual(patcher.patch_step('ShellCommand', self.test_step_1),
                         ('ShellCommand', self.test_step_1))
        self.assertEqual(patcher.patch_step('type', self.test_step_2),
                         ('type', self.test_step_2))
        self.assertEqual(patcher.patch_step('type', self.test_step_3),
                         ('type', self.test_step_3))
        self.assertEqual(patcher.patch_step('type', self.test_step_4),
                         ('type', self.test_step_4))

    def test_branch_skip_string(self):
        config = {'skip_branches': 'a_branch'}
        patcher = Patcher(config)
        self.assertFalse(patcher.is_branch_skipped('my_branch/no_match'))
        self.assertFalse(patcher.is_branch_skipped('a_branc'))
        self.assertTrue(patcher.is_branch_skipped('a_branch_name_with_match'))
        self.assertTrue(patcher.is_branch_skipped('a_branch'))

    def test_branch_skip_list(self):
        config = {'skip_branches': ['a_branch', 'my_branch']}
        patcher = Patcher(config)
        self.assertFalse(patcher.is_branch_skipped('a_branc'))
        self.assertTrue(patcher.is_branch_skipped('a_branch_name_with_match'))
        self.assertTrue(patcher.is_branch_skipped('my_branch/no_match'))
        self.assertTrue(patcher.is_branch_skipped('a_branch'))

    def test_stage_skip_list(self):
        config = {'skip_stages': ['stage1', 'stage2']}
        patcher = Patcher(config)
        self.assertFalse(patcher.is_stage_skipped('stage3'))
        self.assertTrue(patcher.is_stage_skipped('stage1'))
        self.assertTrue(patcher.is_stage_skipped('stage1-bacon'))

    def test_step_skip(self):
        config = {'skip_steps': ['test step', 'other step']}
        patcher = Patcher(config)
        self.assertEqual(patcher.patch_step('type', self.test_step_1),
                         ('type', self.test_step_1))
        self.assertEqual(patcher.patch_step('type', self.test_step_2),
                         ('type', {
                             'name': 'test step',
                             'doStepIf': False,
                             'descriptionDone': 'Temporarily disabled'}))
        self.assertEqual(patcher.patch_step('type', self.test_step_3),
                         ('type', self.test_step_3))
        self.assertEqual(patcher.patch_step('type', self.test_step_4),
                         ('type', {
                             'name': 'test step 4',
                             'doStepIf': False,
                             'descriptionDone': 'Temporarily disabled'}))
