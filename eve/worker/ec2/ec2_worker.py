"""Allow eve to use EC2 workers."""

from buildbot.worker.ec2 import EC2LatentWorker
from twisted.internet import defer, threads


class EveEC2LatentWorker(EC2LatentWorker):
    @defer.inlineCallbacks
    def start_instance(self, build):
        """Start instance after rendering the eve properties"""

        image = yield build.render(self.ami)
        self.image = self.ec2.Image(image)
        self.instance_type = yield build.render(self.instance_type)
        if self.instance is not None:
            raise ValueError('instance active')
        if self.spot_instance:
            res = yield threads.deferToThread(self._request_spot_instance)
        else:
            res = yield threads.deferToThread(self._start_instance)
        defer.returnValue(res)
