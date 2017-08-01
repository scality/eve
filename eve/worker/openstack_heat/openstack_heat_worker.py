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
"""Allow eve to use openstack heat stacks as workers."""

import time

import heatclient
import heatclient.client
from buildbot.worker import AbstractWorker
from buildbot.worker.latent import AbstractLatentWorker
from keystoneauth1 import loading, session
from twisted.internet import defer, threads
from twisted.logger import Logger

MISSING_TIMEOUT = 15 * 60


class HeatLatentWorker(AbstractLatentWorker):
    """Buildbot worker using Openstack heat."""

    logger = Logger('eve.HeatOpenStackLatentWorker')

    quarantine_timeout = quarantine_initial_timeout = 5 * 60
    quarantine_max_timeout = 60 * 60

    def __init__(
            self,
            name,
            password,
            heat_template,
            heat_template_parameters,
            os_auth_url,
            os_username,
            os_password,
            os_project_id,
            os_region_name,
            **kwargs):  # flake8: noqa

        super(HeatLatentWorker, self).__init__(name, password, **kwargs)

        self.heat_template = heat_template
        self.stack_id = None

        if heat_template_parameters is None:
            self.heat_template_parameters = {}
        else:
            self.heat_template_parameters = heat_template_parameters

        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(
            auth_url=os_auth_url,
            username=os_username,
            password=os_password,
            project_name=os_project_id)

        sess = session.Session(auth=auth)
        self.heat_client = heatclient.client.Client(
            '1', session=sess, region_name=os_region_name)

    def reconfigService(self, name, password,
                        **kwargs):
        kwargs.setdefault('missing_timeout', MISSING_TIMEOUT)
        super(HeatLatentWorker, self).reconfigService(name, password, **kwargs)

    @defer.inlineCallbacks
    def start_instance(self, build):
        heat_template = yield build.render(self.heat_template)
        tmp_heat_template_parameters = {}
        for key, value in self.heat_template_parameters.items():
            tmp_heat_template_parameters[key] = yield build.render(value)

        res = yield threads.deferToThread(self._start_instance,
                                          self.name,
                                          heat_template,
                                          tmp_heat_template_parameters)
        defer.returnValue(res)

    def _start_instance(
            self, stack_name, heat_template, heat_template_parameters):

        result = self.heat_client.stacks.create(
            stack_name=stack_name,
            template=heat_template,
            parameters=heat_template_parameters)
        self.stack_id = result['stack']['id']
        stack = self.heat_client.stacks.get(stack_id=self.stack_id)
        while stack.stack_status == 'CREATE_IN_PROGRESS':
            time.sleep(1)
            stack = self.heat_client.stacks.get(stack_id=self.stack_id)

        if stack.stack_status != 'CREATE_COMPLETE':
            raise Exception(stack.stack_status)
        return stack

    def stop_instance(self, fast=False):
        # this allows to call the stack deletion in a thread so we can wait
        # until we are sure they are deleted.
        threads.deferToThread(self._stop_instance, self.stack_id, fast)
        return AbstractWorker.disconnect(self)

    def _stop_instance(self, stack_id, fast):
        stack = self.heat_client.stacks.get(stack_id=stack_id)
        while 'DELETE' not in stack.stack_status:
            # sometimes, the 'DELETE_IN_PROGRESS' status is not set
            # instantaneously after stack.delete() is called. This loop makes
            # sure deletion is in progress or finished before going further.
            stack.delete()
            time.sleep(1)
            stack = self.heat_client.stacks.get(stack_id=stack_id)
        if fast:
            return

        while stack.stack_status == 'DELETE_IN_PROGRESS':
            time.sleep(1)
            stack = self.heat_client.stacks.get(stack_id=stack_id)

        if stack.stack_status != 'DELETE_COMPLETE':
            raise Exception(stack.stack_status)
