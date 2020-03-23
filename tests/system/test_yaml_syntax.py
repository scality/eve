# Copyright 2017 Scality
#
# This file is part of Eve.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
"""This test suite checks end-to-end operation of EVE."""

import unittest

from tests.util.cluster import Cluster
from tests.util.yaml_factory import (
    RawYaml, SingleCommandYaml, YamlFactory, PreMerge
)


class TestYamlSyntax(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cluster = Cluster().start()
        print(cls.cluster.api.url)

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop()
        del cls.cluster

    def setUp(self):
        self.local_repo = self.cluster.clone()

    def tearDown(self):
        del self.local_repo

    def test_empty_yaml(self):
        """Test that the build fails when the YAML file is empty."""
        self.local_repo.push(yaml=RawYaml(''))
        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        self.assertEqual(buildset.result, 'failure')

    def test_skip_if_no_branch_in_yml(self):
        """Test build skipped when branch not covered by eve.yml."""

        self.local_repo.push(yaml=YamlFactory(branches={}, stages={}))
        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        self.assertEqual(buildset.buildrequest.build.result, 'skipped')

    def test_simple_failure(self):
        """Test that build fails if there is an 'exit 1' command in a step."""
        self.local_repo.push(yaml=SingleCommandYaml('exit 1'))
        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        self.assertEqual(buildset.result, 'failure')

        build = buildset.buildrequest.build
        child_buildsets = build.children
        self.assertEqual(len(child_buildsets), 1)
        child_build = child_buildsets[0].buildrequest.build
        self.assertEqual(child_build.result, 'failure')

        failing_step = child_build.first_failing_step
        self.assertEqual(failing_step.state_string, "'exit 1' (failure)")

    def test_simple_success(self):
        """Test that the build succeeds when it is expected to succeed."""
        self.local_repo.push(yaml=SingleCommandYaml('exit 0'))
        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        self.assertEqual(buildset.result, 'success')
        build = buildset.buildrequest.build
        child_buildsets = build.children
        self.assertEqual(len(child_buildsets), 1)
        child_build = child_buildsets[0].buildrequest.build
        self.assertEqual(child_build.result, 'success')

    def test_stage_validity(self):
        """Check behavior with special stage names."""

        steps = [{'ShellCommand': {'command': 'exit 0', 'env': {}}}]

        branch = {'default': {'stage': 'pre-merge'}}
        stage = {'pre-merge': {'worker': {'type': 'local'}, 'steps': steps}}
        self.local_repo.push(yaml=YamlFactory(branches=branch, stages=stage))
        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        self.assertEqual(buildset.result, 'success')

        branch = {'default': {'stage': 'pre-merge'}}
        stage = {
            'bootstrap': {'worker': {'type': 'local'}, 'steps': steps},
            'pre-merge': {'worker': {'type': 'local'}, 'steps': steps},
        }
        self.local_repo.push(yaml=YamlFactory(branches=branch, stages=stage))
        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        self.assertEqual(buildset.result, 'failure')

        branch = {'default': {'stage': 'post-merge'}}
        stage = {'pre-merge': {'worker': {'type': 'local'}, 'steps': steps}}
        self.local_repo.push(yaml=YamlFactory(branches=branch, stages=stage))
        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        self.assertEqual(buildset.result, 'failure')

    def _check_build_and_last_step(self, steps, build_result='success',
                                   last_step_attrs=None):
        self.local_repo.push(yaml=PreMerge(steps=steps))

        buildset = self.cluster.api.force(branch=self.local_repo.branch)
        self.assertEqual(buildset.result, build_result)

        last_step = (
            buildset.buildrequest.build
            .children[0].buildrequest.build
            .steps[-1]
        )
        for attr, value in last_step_attrs.items():
            self.assertEqual(getattr(last_step, attr, None), value)

        return last_step

    def test_boolean_attributes_from_properties(self):
        """Check how one can, and cannot, use properties to set step args."""
        example_values = {
            True: ('yes', 'True'),  # more examples: 'Y', 'true', 'on', '1'
            False: ('N', 'off'),  # more examples: 'no', 'False', '0'
        }

        def set_property(name, value):
            return {
                'SetPropertyFromCommand': {
                    'name': 'Set {} prop'.format(name),
                    'property': '{}'.format(name),
                    'command': 'echo "{}"'.format(value),
                }
            }

        def run_step(**kwargs):
            return {
                'ShellCommand': {
                    'name': 'Run this step',
                    'command': 'exit 0',
                    **kwargs
                }
            }

        for truthy, values in example_values.items():
            for value in values:
                steps = [
                    set_property('someprop', value),
                    run_step(doStepIf='%(prop:someprop)s'),
                ]

                self._check_build_and_last_step(
                    steps,
                    last_step_attrs={
                        'result': 'success' if truthy else 'skipped'
                    },
                )

        # Also works for hiding steps
        for truthy in example_values:
            steps = [
                set_property('someprop', example_values[truthy][0]),
                run_step(hideStepIf='%(prop:someprop)s'),
            ]

            self._check_build_and_last_step(
                steps,
                last_step_attrs={
                    'result': 'success',
                    'hidden': truthy,
                },
            )

        # Check unsupported format
        last_step = self._check_build_and_last_step(
            [run_step(doStepIf='prefixed-%(prop:value)s')],
            build_result='exception',
            last_step_attrs={'result': 'exception'},
        )

        self.assertIn('Invalid format to cast as a boolean:',
                      last_step.rawlog('err_text'))

        # Check unsupported value
        last_step = self._check_build_and_last_step(
            [set_property('someprop', 'not-a-bool'),
             run_step(doStepIf='%(prop:someprop)s')],
            build_result='exception',
            last_step_attrs={'result': 'exception'},
        )

        self.assertIn('Invalid value to cast as boolean: not-a-bool',
                      last_step.rawlog('err_text'))
