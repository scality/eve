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
"""Allow eve to use kubernetes pods as workers."""

import socket
from time import sleep

import yaml
from buildbot import config
from buildbot.interfaces import (LatentWorkerCannotSubstantiate,
                                 LatentWorkerFailedToSubstantiate)
from buildbot.plugins import util
from buildbot.worker.docker import AbstractLatentWorker
from jinja2 import StrictUndefined, Template
from twisted.internet import defer, threads
from twisted.logger import Logger

try:
    from kubernetes import config as kube_config
    from kubernetes import client
    from kubernetes.client.rest import ApiException
except ImportError:
    client = None


class KubePodWorkerCannotSubstantiate(LatentWorkerCannotSubstantiate):
    """Fatal kubernetes pod substantiation error.

    This Exception will put the build in `Exception` state with state_string
    'worker cannot substantiate'.
    It will try to display as much information as possible on this failure to
    the end user.
    This exception doesn't trigger a retry of the calling build.

    """

    def __init__(self, fmt, instance):
        self.pod = instance.metadata.name
        self.status = instance.status
        self.message = '%s: %%s' % (fmt % {
            'pod': self.pod,
            'phase': self.status.phase,
        })

        # Try to get all information on the error
        error = None
        if self.status.phase != 'Running':
            error = self.status.message or self.status.reason

        if not error:
            for container in self.status.container_statuses:
                if container.ready:
                    continue
                if container.state.waiting:
                    msg = (container.state.waiting.message or
                           container.state.waiting.reason)
                    if msg:
                        error = '%s is waiting (%s)' % (container.name,
                                                        msg)
                elif container.state.terminated:
                    msg = (container.state.terminated.message or
                           container.state.terminated.reason)
                    if msg:
                        error = ('%s terminated with exit code \'%d\' (%s)' %
                                 (container.name,
                                  container.state.terminated.exit_code,
                                  msg))

                    if container.state.terminated.reason == 'Error':
                        log = client.CoreV1Api().read_namespaced_pod_log(
                            self.pod,
                            instance.metadata.namespace,
                            container=container.name,
                            tail_lines=10,
                        )
                        error += '\n\n %s' % log

        self.message = self.message % (error or 'Unknown error')
        super(KubePodWorkerCannotSubstantiate, self).__init__(self.message)


class EveKubeLatentWorker(AbstractLatentWorker):

    logger = Logger('eve.workers.EveKubeLatentWorker')
    instance = None
    _poll_resolution = 2

    def load_config(self):
        try:
            kube_config.load_incluster_config()
        except Exception:
            kube_config.load_kube_config()
        if self.kubeConfig:
            for config_key, value in self.kubeConfig.items():
                setattr(client.configuration, config_key, value)

    def checkConfig(self, name, password, master_fqdn, pb_port,
                    namespace, node_affinity, max_memory, max_cpus,
                    microservice_gitcache, active_deadline, kube_config,
                    **kwargs):
        """Ensure we have the kubernetes client available."""
        # Set build_wait_timeout to 0 if not explicitly set: Starting a
        # container is almost immediate, we can afford doing so for each build.
        kwargs.setdefault('build_wait_timeout', 0)
        if not client:
            config.error('The python module \'kubernetes>=1\' is needed to '
                         'use a KubeLatentWorker')
        AbstractLatentWorker.checkConfig(self, name, password, **kwargs)

    def reconfigService(self, name, password, master_fqdn, pb_port,
                        namespace, node_affinity, max_memory, max_cpus,
                        microservice_gitcache, active_deadline, kube_config,
                        **kwargs):
        # Set build_wait_timeout to 0 if not explicitly set: Starting a
        # container is almost immediate, we can afford doing so for each build.
        kwargs.setdefault('build_wait_timeout', 0)
        password = password or self.getRandomPass()
        self.master_fqdn = master_fqdn or socket.getfqdn()
        self.namespace = namespace or 'default'
        self.node_affinity = node_affinity
        self.kubeConfig = kube_config
        self.pb_port = pb_port
        self.max_memory = max_memory
        self.max_cpus = max_cpus
        self.microservice_gitcache = microservice_gitcache
        self.deadline = active_deadline
        return AbstractLatentWorker.reconfigService(self, name, password,
                                                    **kwargs)

    def get_pod_config(self, build):
        """Render and load valid pod template from build."""
        try:
            template = Template(build.getProperty('worker_template'),
                                undefined=StrictUndefined)
            rendered_body = template.render(
                images=build.getProperty('worker_images'),
                vars=build.getProperty('worker_vars'),
            )
        except Exception as ex:
            raise LatentWorkerCannotSubstantiate(
                'Unable to render %s (%s)' % (self.template_path, ex))

        try:
            pod = yaml.load(rendered_body)
        except Exception as ex:
            raise LatentWorkerCannotSubstantiate(
                'Unable to read yaml from %s (%s)' % (self.template_path,
                                                      ex))

        try:
            assert pod['kind'] == 'Pod'
            assert pod['spec']['containers']
        except Exception as ex:
            raise LatentWorkerCannotSubstantiate(
                '%s is not a valid Kuberbetes pod '
                'definition (%s)' % (self.template_path, ex))

        return pod

    def enforce_restart_policy(self, pod):
        """Prevent kubernetes to restart any worker pod."""
        if 'restartPolicy' in pod['spec']:
            if pod['spec']['restartPolicy'] != 'Never':
                raise LatentWorkerCannotSubstantiate(
                    'restartPolicy must be set to \'Never\' '
                    '(restart of buildbot-worker is not '
                    'supported) in %s' % self.template_path)
        else:
            pod['spec']['restartPolicy'] = 'Never'

    def enforce_affinity_policy(self, pod):
        """Prevent user from overriding affinity set by eve for workers."""
        if 'affinity' in pod['spec']:
            raise LatentWorkerCannotSubstantiate(
                'the affinity that is specified in the worker '
                'conflicts with Eve\'s pod placement policy. '
                'Please remove this section from the '
                'worker yaml file in %s' % self.template_path)

        if self.node_affinity:
            pod['spec']['affinity'] = {
                'nodeAffinity': {
                    'requiredDuringSchedulingIgnoredDuringExecution': {
                        'nodeSelectorTerms': [{
                            'matchExpressions': [{
                                'key': self.node_affinity.key,
                                'operator': 'In',
                                'values': [self.node_affinity.value]}]}]}}}

    def enforce_gitconfig(self, pod):
        """Implicitly set the git config in every containers."""
        if not self.microservice_gitcache:
            return
        volume = {'name': 'gitconfig', 'configMap': {'name': 'gitconfig'}}
        volume_mount = {'name': 'gitconfig', 'mountPath': '/etc/gitconfig',
                        'subPath': 'gitconfig'}
        pod['spec'].setdefault('volumes', [])
        pod['spec']['volumes'].append(volume)
        for container in pod['spec']['containers']:
            container.setdefault('volumeMounts', [])
            container['volumeMounts'].append(volume_mount)

    def add_common_worker_env_vars(self, pod, build):
        """Set eve workers env vars in each containers of the pod."""
        stage_name = build.getProperty('stage_name')

        for container in pod['spec']['containers']:
            container.setdefault('env', [])
            container['env'].extend([
                {'name': 'BUILDMASTER', 'value': self.master_fqdn},
                {'name': 'BUILDMASTER_PORT', 'value': self.pb_port},
                {'name': 'RUNNING_IN_CI', 'value': '1'},
                {'name': 'STAGE', 'value': stage_name},
                {'name': 'WORKERNAME', 'value': self.name},
                {'name': 'WORKERPASS', 'value': self.password},
            ])

    def add_common_worker_metadata(self, pod, build):
        """Add eve-related metadata to pod to easily identify them in kube."""
        buildid = build.getProperty('buildnumber')
        buildnumber = build.getProperty('bootstrap')
        stage_name = build.getProperty('stage_name')

        pod.setdefault('metadata', {}).setdefault('labels', {})
        pod['metadata']['name'] = 'worker-%d-%d' % (buildnumber, buildid)
        pod['metadata']['labels']['buildnumber'] = str(buildnumber)
        pod['metadata']['labels']['buildid'] = str(buildid)
        pod['metadata']['labels']['workername'] = self.name
        pod['metadata']['labels']['stage'] = stage_name
        pod['metadata']['labels']['app'] = 'eve'
        pod['metadata']['labels']['service'] = 'worker'

    def enforce_resource_limits(self, pod):
        """Enforce resource request limits."""
        total = {'requests': {'cpu': 0, 'memory': 0},
                 'limits': {'cpu': 0, 'memory': 0}}

        def resource_limit(kind, d, spec):
            if kind == 'memory':
                conv = util.convert_to_bytes
                bound = self.max_memory
                unit = 'RAM'
            elif kind == 'cpu':
                conv = util.convert_to_cpus
                bound = self.max_cpus
                unit = 'CPUs'
            else:
                raise ValueError('limits must be memory or cpu')

            try:
                if conv(d[kind]) > conv(bound):
                    raise LatentWorkerCannotSubstantiate(
                        'Can\'t set request/limit to %s %s (max allowed '
                        'is %s).' % (d[kind], unit, bound))
            except KeyError:
                raise LatentWorkerCannotSubstantiate(
                    'All cpu & memory requests/limits must be set!')

            total[spec][kind] += conv(d[kind])

        # Enforce per-container limits
        for container in pod['spec']['containers']:
            container.setdefault('resources', {})
            requests = container['resources'].setdefault('requests', {})
            limits = container['resources'].setdefault('limits', {})

            resource_limit('memory', requests, 'requests')
            resource_limit('memory', limits, 'limits')
            resource_limit('cpu', requests, 'requests')
            resource_limit('cpu', limits, 'limits')

        # Enforce pod-wide limits
        if (total['requests']['memory'] >
                util.convert_to_bytes(self.max_memory)):
            raise LatentWorkerCannotSubstantiate(
                'Total memory requested for pod can\'t exceed %s!' %
                self.max_memory)
        if (total['limits']['memory'] >
                util.convert_to_bytes(self.max_memory)):
            raise LatentWorkerCannotSubstantiate(
                'Total memory limit for pod can\'t exceed %s!' %
                self.max_memory)
        if (total['requests']['cpu'] >
                util.convert_to_cpus(self.max_cpus)):
            raise LatentWorkerCannotSubstantiate(
                'Total cpu requested for pod can\'t exceed %s!' %
                self.max_cpus)
        if (total['limits']['cpu'] >
                util.convert_to_cpus(self.max_cpus)):
            raise LatentWorkerCannotSubstantiate(
                'Total cpu limit for pod can\'t exceed %s!' %
                self.max_cpus)

    def enforce_active_deadline(self, pod):
        """Prevent stuck pod by setting an active deadline on it."""
        if 'activeDeadlineSeconds' in pod['spec']:
            if pod['spec']['activeDeadlineSeconds'] > self.deadline:
                raise LatentWorkerCannotSubstantiate(
                    'activeDeadlineSeconds must be set to a value lower than '
                    '%d in %s' % (self.deadline, self.template_path))
        else:
            pod['spec']['activeDeadlineSeconds'] = self.deadline

    @defer.inlineCallbacks
    def start_instance(self, build):
        if self.instance is not None:
            raise ValueError('instance active')
        if self.registration is not None:
            self.pb_port = str(self.registration.getPBPort())

        self.template_path = build.getProperty('worker_path')

        try:
            pod = self.get_pod_config(build)
            self.enforce_restart_policy(pod)
            self.enforce_affinity_policy(pod)
            self.enforce_gitconfig(pod)
            self.add_common_worker_env_vars(pod, build)
            self.add_common_worker_metadata(pod, build)
            self.enforce_resource_limits(pod)
            self.enforce_active_deadline(pod)
        except LatentWorkerCannotSubstantiate:
            raise
        except Exception as ex:
            raise LatentWorkerCannotSubstantiate(
                'Unable to validate pod config %s (%s)' % (self.template_path,
                                                           ex))

        res = yield threads.deferToThread(
            self._thd_start_instance,
            self.namespace,
            pod
        )
        defer.returnValue(res)

    def _thd_start_instance(self, namespace, pod):
        self.load_config()
        # TODO block until buildbot-worker has reported back
        # otherwise unable to log pod generation errors
        self.logger.debug('Starting pod with config:\n%s' %
                          yaml.dump(pod, default_flow_style=False))
        try:
            instance = client.CoreV1Api().create_namespaced_pod(namespace,
                                                                pod)
        except ApiException as ex:
            raise LatentWorkerCannotSubstantiate(
                'Failed to create pod %s: %s' % (pod.metadata.name,
                                                 ex.reason))

        # Wait for pod to be running
        duration = 0
        while instance.status.phase in ['Pending', None]:
            sleep(self._poll_resolution)
            duration += self._poll_resolution
            try:
                instance = client.CoreV1Api().read_namespaced_pod_status(
                    instance.metadata.name, namespace)
            except ApiException as ex:
                raise LatentWorkerFailedToSubstantiate(
                    'Pod %s went missing: %s' % (instance.metadata.name,
                                                 ex.reason))

        # Ensure the pod is running
        if instance.status.phase != 'Running':
            raise KubePodWorkerCannotSubstantiate(
                'Pod %(pod)s is not running (%(phase)s)', instance)
        self.logger.debug('Pod created, id: %s...' %
                          instance.metadata.name)

        self.instance = instance
        return instance.metadata.name

    def stop_instance(self, fast=False):
        assert not fast
        if self.instance is None:
            # be gentle. Something may just be trying to alert us that an
            # instance never attached, and it's because, somehow, we never
            # started.
            return defer.succeed(None)
        instance = self.instance
        self.instance = None
        return threads.deferToThread(self._thd_stop_instance, instance, fast)

    def _thd_stop_instance(self, instance, fast):
        self.load_config()
        self.logger.debug('Deleting pod %s...' % instance.metadata.name)
        client.CoreV1Api().delete_namespaced_pod(instance.metadata.name,
                                                 instance.metadata.namespace,
                                                 client.V1DeleteOptions())
