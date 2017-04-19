import yaml


class YamlFactory(object):
    def __init__(self, version='0.2', branches=None, stages=None):
        self.version = version
        self.branches = branches
        self.stages = stages

    def filedump(self, file_):
        data = dict(
            version=self.version,
            branches=self.branches,
            stages=self.stages, )
        print data
        with open(file_, 'w') as fhandle:
            yaml.dump(data, fhandle, default_flow_style=False)


class PreMerge(YamlFactory):
    def __init__(self, steps, worker=None):
        branches = {'default': {'stage': 'pre-merge'}}
        if worker is None:
            worker = {'type': 'local'}
        stages = {'pre-merge': {'worker': worker, 'steps': steps}}

        super(PreMerge, self).__init__(branches=branches, stages=stages)


class EmptyYaml(YamlFactory):
    def filedump(self, file_):
        with open(file_, 'w') as fhandle:
            fhandle.write('')


class ZeroStageYaml(YamlFactory):
    def __init__(self):
        super(ZeroStageYaml, self).__init__(branches={}, stages={})


class SingleCommandYaml(PreMerge):
    def __init__(self, command='exit 0', worker=None):
        shell_command_step = {'ShellCommand': {'command': command}}
        super(SingleCommandYaml, self).__init__(
            steps=[shell_command_step], worker=worker)
