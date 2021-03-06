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
"""Enable local jobs in buildbot."""
from os import getcwd, path, walk

import yaml
from buildbot.config import BuilderConfig
from buildbot.plugins import schedulers, util
from buildbot.process.factory import BuildFactory
from twisted.logger import Logger


def local_jobs(workers):
    """Load yaml local jobs in Eve config."""
    local_dirpath = path.join(getcwd(), util.env.LOCAL_JOBS_DIRPATH)
    builders = []
    scheds = []
    print(local_dirpath, path.isdir(local_dirpath))
    if path.isdir(local_dirpath):
        for job_conf_file in next(walk(local_dirpath))[2]:
            filename = path.join(local_dirpath, job_conf_file)
            try:
                blder, schdler = define_local_job(
                    filename, workers, util.env.SUFFIX)
                builders.append(blder)
                scheds.append(schdler)
            except Exception as error:
                raise Exception('There was an error while loading local job '
                                '%r, aborting (%s)' % (job_conf_file, error))
    return builders, scheds


def define_local_job(job_conf_file, workers, suffix):
    # pylint: disable=too-many-locals
    """Add a single local job to eve config file."""
    logger = Logger('eve.common.define_local_job')

    with open(job_conf_file) as raw_conf:
        conf = yaml.load(raw_conf)
    default_name = path.split(job_conf_file)[-1]
    default_name = path.splitext(default_name)[0]

    factory = BuildFactory()

    logger.debug('creating a new build factory for local job {job}',
                 job=job_conf_file)
    for step in conf['steps']:
        step_type, params = next(iter(step.items()))
        logger.debug('adding step {step} with params: {params}',
                     step=step_type, params=params)
        factory.addStep(util.step_factory({}, step_type, **params))

    builder = conf.get('builder', {})
    builder_name = \
        builder.pop('name', '{0}-{1}'.format(default_name, suffix))
    logger.debug('creating builder {builder} with params: {params}',
                 builder=builder_name, params=builder)
    logger.debug('workers: {workers}', workers=[lw.name for lw in workers])
    builder = BuilderConfig(
        name=builder_name,
        factory=factory,
        workernames=[lw.name for lw in workers],
        **builder
    )
    scheduler = conf.get('scheduler', {})
    _type = scheduler.pop('type', 'Periodic')
    _cls = getattr(schedulers, _type)
    scheduler_name = \
        scheduler.pop(
            'name', '{0}-scheduler-{1}'.format(default_name, suffix))
    logger.debug('creating scheduler {scheduler} ({scheduler_type}) with '
                 'params: {params}',
                 scheduler=scheduler_name,
                 scheduler_type=_type,
                 params=scheduler)
    scheduler = _cls(
        name=scheduler_name,
        builderNames=[builder_name],
        **scheduler
    )
    return builder, scheduler
