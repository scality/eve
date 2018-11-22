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

from buildbot.plugins import util


class KubernetesPodBuildOrder(util.BaseDockerBuildOrder):
    """Base class representing a build to trigger on a Kubernetes pod.

    Build/pull all needed docker images and setup all properties required by
    the kub pod worker.
    """

    def setup_properties(self):
        super(KubernetesPodBuildOrder, self).setup_properties()

        worker_path = self._worker['path']
        self.properties['worker_path'] = (worker_path,
                                          'KubernetesPodBuildOrder')

        full_worker_path = '%s/build/%s' % (
            self.properties['master_builddir'][0], worker_path)

        with open(full_worker_path, 'r') as template:
            self.properties['worker_template'] = (
                template.read(), 'KubernetesPodBuildOrder')

        images = self._worker.get('images', {})
        image_vars = {}
        for (name, params) in images.iteritems():
            if isinstance(params, dict):
                context = params.get('context')
                if context is None or not isinstance(context, str):
                    raise ValueError(
                        'Missing or incorrect context arg type '
                        'in image definition.')

                dockerfile = params.get('dockerfile')
                if dockerfile is not None and not isinstance(dockerfile, str):
                    raise ValueError(
                        'Incorrect arg dockerfile type in image definition.')

                image_vars[name] = self._build_image(name, context, dockerfile)

            elif isinstance(params, basestring):
                image_vars[name] = self._build_image(name, params)

            else:
                raise ValueError('Unexpected data type in images. '
                                 'type: %s' % type(params))

        self.properties['worker_images'] = (image_vars,
                                            'KubernetesPodBuildOrder')
        self.properties['worker_vars'] = (self._worker.get('vars', {}),
                                          'KubernetesPodBuildOrder')

        self.properties['worker_service'] = (self._worker.get('service', None),
                                             'KubernetesPodBuildOrder')
