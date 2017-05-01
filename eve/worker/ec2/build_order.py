from buildbot.plugins import util


class EC2BuildOrder(util.BaseBuildOrder):
    """Base class representing a build to trigger on an EC2 instance
    (Scheduler, properties and EC2 config)
    """
    def setup_properties(self):
        super(EC2BuildOrder, self).setup_properties()

        self.properties.update({
            'ec2_ami': self._worker.get('ami'),
            'ec2_instance_type': self._worker.get('instance_type')
        })