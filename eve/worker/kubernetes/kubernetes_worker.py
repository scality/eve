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

SERVICE_POD_TEMPLATE = """
---
apiVersion: v1
kind: Pod
metadata:
  name: "service-pod"
  labels:
    worker_pod_name: "{{ worker_pod_name }}"
    uuid: "{{ uuid }}"
spec:
  activeDeadlineSeconds: 300
  restartPolicy: Never
  containers:
    - name: kube-worker-service
      image: "{{ image }}"
      resources:
        requests:
          cpu: "500m"
          memory: "1Gi"
        limits:
          cpu: "500m"
          memory: "1Gi"
      env:
        - name: BUILDID
          value: "{{ buildid }}"
        - name: BUILDNUMBER
          value: "{{ buildnumber }}"
        - name: NAMESPACES
          value: "{{ namespaces|join(' ') }}"
        - name: UUID
          value: "{{ uuid }}"
        {% for key in service_requests.keys() %}
        - name: "{{ key }}"
          value: "{{ service_requests[key] }}"
        {% endfor %}
      {% if service_data %}
      envFrom:
        - secretRef:
            name: "{{ service_data }}"
      {% endif %}
      args: [ "init" ]
"""


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
                    msg = (container.state.waiting.message
                           or container.state.waiting.reason)
                    if msg:
                        error = '%s is waiting (%s)' % (container.name,
                                                        msg)
                elif container.state.terminated:
                    msg = (container.state.terminated.message
                           or container.state.terminated.reason)
                    if msg:
                        error = ('%s terminated with exit code \'%d\' (%s)' %
                                 (container.name,
                                  container.state.terminated.exit_code,
                                  msg))

                    if container.state.terminated.reason == 'Error':
                        try:
                            log = client.CoreV1Api().read_namespaced_pod_log(
                                self.pod,
                                instance.metadata.namespace,
                                container=container.name,
                                tail_lines=100,
                            )
                        except ApiException:
                            log = 'container is gone, log is not available'
                        error += '\ncontainer last 100 log lines:\n\n%s' % log

        self.message = self.message % (error or 'Unknown error')
        super(KubePodWorkerCannotSubstantiate, self).__init__(self.message)


class EveKubeLatentWorker(AbstractLatentWorker):

    logger = Logger('eve.workers.EveKubeLatentWorker')
    instance = None
    _poll_resolution = 2
    service_pod = None

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
                    gitconfig, active_deadline, kube_config,
                    service, service_data, **kwargs):
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
                        gitconfig, active_deadline, kube_config,
                        service, service_data, **kwargs):
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
        self.deadline = active_deadline
        self.gitconfig = gitconfig
        self.service = service
        self.service_data = service_data
        return AbstractLatentWorker.reconfigService(self, name, password,
                                                    **kwargs)

    def get_pod_config(self, name, source, variables):
        """Render and load valid pod template."""
        try:
            template = Template(source, undefined=StrictUndefined)
            rendered_body = template.render(variables)
        except Exception as ex:
            raise LatentWorkerCannotSubstantiate(
                'Unable to render %s (%s)' % (name, ex))

        try:
            pod = yaml.load(rendered_body)
        except Exception as ex:
            raise LatentWorkerCannotSubstantiate(
                'Unable to read yaml from %s (%s)' % (name, ex))

        try:
            assert pod['kind'] == 'Pod'
            assert pod['spec']['containers']
        except Exception as ex:
            raise LatentWorkerCannotSubstantiate(
                '%s is not a valid Kuberbetes pod '
                'definition (%s)' % (name, ex))

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
        if not self.gitconfig:
            return

        volume = {
            'name': 'gitconfig',
            'configMap': {'name': self.gitconfig}
        }
        volume_mount = {
            'name': 'gitconfig',
            'mountPath': '/etc/gitconfig',
            'subPath': 'gitconfig'
        }
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

    @defer.inlineCallbacks
    def interpolate_pod(self, pod, build):
        """Interpolate properties inside the pod description file."""
        interpolated_pod = yield build.render(
            util.replace_with_interpolate(pod))
        defer.returnValue(interpolated_pod)

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
        if (total['requests']['memory']
                > util.convert_to_bytes(self.max_memory)):
            raise LatentWorkerCannotSubstantiate(
                'Total memory requested for pod can\'t exceed %s!' %
                self.max_memory)
        if (total['limits']['memory']
                > util.convert_to_bytes(self.max_memory)):
            raise LatentWorkerCannotSubstantiate(
                'Total memory limit for pod can\'t exceed %s!' %
                self.max_memory)
        if (total['requests']['cpu']
                > util.convert_to_cpus(self.max_cpus)):
            raise LatentWorkerCannotSubstantiate(
                'Total cpu requested for pod can\'t exceed %s!' %
                self.max_cpus)
        if (total['limits']['cpu']
                > util.convert_to_cpus(self.max_cpus)):
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

    def configure_service_pod(self, pod, build):
        """Define the pod that init/teardown an external service."""

        self.service_pod = None

        worker_service = build.getProperty('worker_service')

        if worker_service is None:
            return

        if not self.service:
            # configuration does not provide any service
            raise LatentWorkerCannotSubstantiate(
                'The worker is requesting access to a Kubernetes '
                'cluster but Eve is not configured to provide one; '
                'either remove the `service` section from the worker '
                'or reconfigure Eve.')

        buildid = build.getProperty('buildnumber')
        buildnumber = build.getProperty('bootstrap')
        repository = build.getProperty('repository')

        # retrieve unique user id and create namespace ids
        uuid = build.getProperty('worker_uuid')
        ns_plain = worker_service.get('namespaces', [])
        ns_hash = [util.create_hash(repository, ns, buildnumber, buildid)
                   for ns in ns_plain]

        # store in properties
        for (plain, hashed) in zip(ns_plain, ns_hash):
            build.setProperty(plain, hashed, "Build")

        self.service_pod = self.get_pod_config(
            'SERVICE_POD_TEMPLATE', SERVICE_POD_TEMPLATE, {
                'buildid': buildid,
                'buildnumber': buildnumber,
                'image': self.service,
                'namespaces': ns_hash,
                'service_data': self.service_data,
                'service_requests': worker_service.get('requests', {}),
                'uuid': uuid,
                'worker_pod_name': 'worker-%d-%d' % (buildnumber, buildid),
            }
        )
        self.enforce_affinity_policy(self.service_pod)
        self.add_common_worker_env_vars(self.service_pod, build)
        self.add_common_worker_metadata(self.service_pod, build)

        # attach credentials to all containers in the worker pod
        pod['spec'].setdefault('volumes', [])
        pod['spec']['volumes'].append({
            'name': 'kubeconfig', 'secret': {
                'secretName': uuid}
        })
        for container in pod['spec']['containers']:
            container.setdefault('env', [])
            container['env'].extend([
                {'name': 'KUBECONFIG', 'value': '/.kubeconfig'},
            ])
            container.setdefault('volumeMounts', [])
            container['volumeMounts'].append({
                'name': 'kubeconfig',
                'readOnly': True,
                'mountPath': '/.kubeconfig',
                'subPath': 'kubeconfig'
            })

    @defer.inlineCallbacks
    def start_instance(self, build):
        if self.instance is not None:
            raise ValueError('instance active')
        if self.registration is not None:
            self.pb_port = str(self.registration.getPBPort())

        self.template_path = build.getProperty('worker_path')

        try:
            pod = self.get_pod_config(
                self.template_path,
                build.getProperty('worker_template'),
                variables={
                    'images': build.getProperty('worker_images'),
                    'vars': build.getProperty('worker_vars'),
                }
            )
            repository = build.getProperty('repository')
            uuid = util.create_hash(repository, self.name)
            build.setProperty("worker_uuid", uuid, "Build")
            self.enforce_restart_policy(pod)
            self.enforce_affinity_policy(pod)
            self.enforce_gitconfig(pod)
            self.add_common_worker_env_vars(pod, build)
            self.add_common_worker_metadata(pod, build)
            self.enforce_resource_limits(pod)
            self.enforce_active_deadline(pod)
            self.configure_service_pod(pod, build)
            pod = yield self.interpolate_pod(pod, build)
        except LatentWorkerCannotSubstantiate:
            raise
        except Exception as ex:
            raise LatentWorkerCannotSubstantiate(
                'Unable to validate pod config %s (%s)' % (self.template_path,
                                                           ex))

        res = yield threads.deferToThread(
            self._thd_start_instance,
            pod
        )
        defer.returnValue(res)

    def _thd_start_pod(self, pod, wait_for_completion=False):
        """Start the pod resource provided as a dictionnary.

        This method will block until the pod has reached one
        of the stable condition RUNNING/COMPLETE/FAILED.

        """
        pod_name = pod.get('metadata', {}).get('name', 'no_name')
        self.logger.debug('Starting pod %r with config:\n%s' % (
                          pod_name,
                          yaml.safe_dump(pod, default_flow_style=False)))
        try:
            instance = client.CoreV1Api().create_namespaced_pod(
                self.namespace, pod)
        except ApiException as ex:
            raise LatentWorkerCannotSubstantiate(
                'Failed to create pod %s: %s' % (pod_name, ex.reason))

        pending = [None, 'Pending', 'Unknown']
        if wait_for_completion:
            pending.append('Running')
        duration = 0
        while instance.status.phase in pending:
            sleep(self._poll_resolution)
            duration += self._poll_resolution
            try:
                instance = client.CoreV1Api().read_namespaced_pod_status(
                    instance.metadata.name, self.namespace)
            except ApiException as ex:
                if wait_for_completion:
                    # pod may have completed
                    break

                raise LatentWorkerFailedToSubstantiate(
                    'Pod %s went missing: %s' % (instance.metadata.name,
                                                 ex.reason))

        # Ensure the pod is running or has run successfully
        if instance.status.phase in [None, 'Pending', 'Failed', 'Unknown']:
            try:
                raise KubePodWorkerCannotSubstantiate(
                    'Creating Pod %(pod)s failed (%(phase)s)', instance)
            finally:
                self.delete_pod(instance.metadata.name)

        if wait_for_completion:
            self.delete_pod(instance.metadata.name)

        return instance.metadata.name

    def service_run(self, stage):
        if self.service_pod:
            self.service_pod['spec']['containers'][0]['args'] = [stage]
            self.service_pod['metadata']['name'] = '%s-service-%s' % (
                self.service_pod['metadata']['labels']['worker_pod_name'],
                stage
            )
            self._thd_start_pod(self.service_pod, wait_for_completion=True)

    def service_init(self):
        self.logger.debug('Run kube service init (%s)...' % self.service)
        self.service_run('init')

    def service_teardown(self):
        self.logger.debug('Run kube service teardown (%s)...' % self.service)
        try:
            self.service_run('teardown')
        except Exception:
            # fail silently on teardown to prevent
            # hiding previous potential exceptions
            pass

    def delete_pod(self, name):
        self.logger.debug('deleting kube pod %s...' % name)
        max_wait_time = 240
        duration = 0
        try:
            client.CoreV1Api().delete_namespaced_pod(name,
                                                     self.namespace,
                                                     client.V1DeleteOptions())
            # Ensure that deleted pods are actually gone and not
            # on terminating phase. This allow us to avoid attaching undesired
            # buildbot-workers on new builds.
            while duration < max_wait_time:
                instance = client.CoreV1Api().read_namespaced_pod_status(
                    name,
                    self.namespace)
                self.logger.info('kube pod %s still in phase %s' %
                                 (name, instance.status.phase))
                sleep(self._poll_resolution)
                duration += self._poll_resolution

            self.logger.info('max wait time reached forcing'
                             ' deletion of pod %s' % name)
            client.CoreV1Api().delete_namespaced_pod(
                name,
                self.namespace,
                client.V1DeleteOptions(grace_period_seconds=0))
        except ApiException as ex:
            if ex.status == 404:
                self.logger.info('kube pod %s was successfully deleted' % name)
            else:
                self.logger.debug('unable to delete kube pod %s...' % name)
            pass

    def _thd_start_instance(self, pod):
        self.load_config()

        self.service_init()
        self.instance = self._thd_start_pod(pod)

        return self.instance

    def stop_instance(self, fast=False):
        assert not fast
        instance = self.instance
        self.instance = None
        return threads.deferToThread(self._thd_stop_instance, instance, fast)

    def _thd_stop_instance(self, instance, fast):
        self.logger.debug('Deleting worker %s...' % instance)
        self.load_config()
        try:
            if instance:
                self.delete_pod(instance)
        finally:
            self.service_teardown()
