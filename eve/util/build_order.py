class BaseBuildOrder(object):
    """Base class representing a build to trigger
    (Scheduler and properties)
    """

    def __init__(self, scheduler, git_repo, stage_name, stage,
                 worker, parent_step):
        self.git_repo = git_repo
        self.scheduler = scheduler
        self._stage_name = stage_name
        self._stage = stage
        self._worker = worker
        self._parent_step = parent_step

        self.properties = {}
        self.preliminary_steps = []

        self.setup_properties()

    def setup_properties(self):
        """
        Setup additional properties
        :return: None
        """
        properties = self._parent_step.getProperties()
        self.properties = {
            k: v[0] for k, v in properties.asDict().iteritems()
        }
        self.properties.update({
            'stage_name': self._stage_name,
            'reason': self._stage_name,
            'git_reference': self.git_repo,
            'git_repo': self.git_repo,
        })
