"""Classes to dynamically generate eve YAML files
"""

import yaml


class RawYaml(object):
    def __init__(self, yaml_text):
        """
        Generates a YAML file from the text given in parameter

          Notes:
              Nothing prevents from having a syntaxically incorrect text.
              Therfore, you can use this class to generate broken YAML files.

        Args:
            yaml_text (str): The text to store in the YAML file
        """
        self.yaml_text = yaml_text

    def filedump(self, filename):
        """
        Dump the YAML structrure to a file

        Args:
            filename: the path to the file where the YAML will be dumped
        """
        with open(filename, 'w') as fhandle:
            fhandle.write(self.yaml_text)


class YamlFactory(RawYaml):
    def __init__(self, version='0.2', branches=None, stages=None):
        """
        Base class to generate a syntaxically correct eve yaml file

        Args:
            version (str): the eve file version number (e.g 0.1 or 0.2)
            branches (dict): the branch patterns covered by the YAML file as
                             well as their corresponding stages.
                             {
                                'feature/*': {'stage': 'pre-merge'}
                                'default': {'stage': 'post-merge'}
                             }
            stages (dict): the stage specifications (see eve's user doc).
        """
        data = dict(version=version, branches=branches, stages=stages)
        yaml_text = yaml.dump(data, default_flow_style=False)
        super(YamlFactory, self).__init__(yaml_text=yaml_text)


class PreMerge(YamlFactory):
    def __init__(self, steps, worker=None):
        """
        Generate a YAML file with a single stage called 'pre-merge'.

        Args:
            steps (list): the steps of the pre-merge stage
            worker (dict): the worker definition. e.g. default :
                           {'type': 'local'}
        """
        branches = {'default': {'stage': 'pre-merge'}}
        if worker is None:
            worker = {'type': 'local'}
        stages = {'pre-merge': {'worker': worker, 'steps': steps}}

        super(PreMerge, self).__init__(branches=branches, stages=stages)


class SingleCommandYaml(PreMerge):
    def __init__(self, command='exit 0', worker=None):
        """
        Generate a YAML file with a single stage that runs a single command.

        Args:
            command (str): the command to run
            worker (dict): the worker definition. e.g. default :
                           {'type': 'local'}
        """
        shell_command_step = {'ShellCommand': {'command': command}}
        super(SingleCommandYaml, self).__init__(
            steps=[shell_command_step], worker=worker)
