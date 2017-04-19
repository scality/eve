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
"""Classes to dynamically generate eve YAML files."""

import yaml


class RawYaml(object):
    def __init__(self, yaml_text):
        """Generate a YAML file from the text given in parameter.

        Notes:
            Nothing prevents from having a syntaxically incorrect text.
            Therfore, you can use this class to generate broken YAML files.

        Args:
            yaml_text (str): The text to store in the YAML file.

        """
        self.yaml_text = yaml_text

    def filedump(self, filename):
        """Dump the YAML structrure to a file.

        Args:
            filename: The path to the file where the YAML will be dumped.

        """
        with open(filename, 'w') as fhandle:
            fhandle.write(self.yaml_text)


class YamlFactory(RawYaml):
    def __init__(self, version='0.2', branches=None, stages=None):
        """Generate a syntaxically correct eve yaml file.

        Args:
            version (str): The eve file version number (e.g 0.1 or 0.2).
            branches (dict): The branch patterns covered by the YAML file as
                well as their corresponding stages.
                {
                    'feature/*': {'stage': 'pre-merge'}
                    'default': {'stage': 'post-merge'}
                }
            stages (dict): The stage specifications (see eve's user doc).

        """
        data = dict(version=version, branches=branches, stages=stages)
        yaml_text = yaml.dump(data, default_flow_style=False)
        super(YamlFactory, self).__init__(yaml_text=yaml_text)


class PreMerge(YamlFactory):
    def __init__(self, steps, worker=None):
        """Generate a YAML file with a single stage called 'pre-merge'.

        Args:
            steps (list): The steps of the pre-merge stage.
            worker (dict): The worker definition (default: {'type': 'local'}).

        """
        branches = {'default': {'stage': 'pre-merge'}}
        if worker is None:
            worker = {'type': 'local'}
        stages = {'pre-merge': {'worker': worker, 'steps': steps}}

        super(PreMerge, self).__init__(branches=branches, stages=stages)


class SingleCommandYaml(PreMerge):
    def __init__(self, command='exit 0', worker=None):
        """Generate a YAML file with a single stage that runs a single command.

        Args:
            command (str): The command to run.
            worker (dict): The worker definition (default: {'type': 'local'}).

        """
        shell_command_step = {'ShellCommand': {'command': command}}
        super(SingleCommandYaml, self).__init__(
            steps=[shell_command_step], worker=worker)


class LocalJobsYaml(YamlFactory):
    def filedump(self, file_):
        data = dict(
            steps=[{
                'ShellCommand': {
                    'command': 'exit 0'
                }
            }],
            scheduler={'type': 'Periodic',
                       'periodicBuildTimer': '5'})
        with open(file_, 'w') as fhandle:
            yaml.dump(data, fhandle, default_flow_style=False)
