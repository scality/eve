from ...utils.build_order import BaseBuildOrder


class OpenStackBuildOrder(BaseBuildOrder):
    """Base class representing a build to trigger on an OpenStack instance
    (Scheduler, properties and OpenStack config)
    """

    DEFAULT_IMAGE = 'Ubuntu 14.04 LTS (Trusty Tahr) (PVHVM)'
    DEFAULT_FLAVOR = 'general1-4'
    """See https://developer.rackspace.com/docs/cloud-servers/v2/general-api-info/flavors/."""  # noqa: E501, pylint: disable=line-too-long

    def setup_properties(self):
        super(OpenStackBuildOrder, self).setup_properties()

        self.properties.update({
            'worker_path': self._worker['path'],
            'openstack_image': self._worker.get('image', self.DEFAULT_IMAGE),
            'openstack_flavor': self._worker.get('flavor', self.DEFAULT_FLAVOR)
        })
