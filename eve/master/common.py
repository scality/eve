"""Buildbot configuration common to all eve machines."""
from os import environ, path, walk

import yaml
from buildbot.config import BuilderConfig
from buildbot.plugins import schedulers, steps
from buildbot.process.factory import BuildFactory
from buildbot.process.properties import Interpolate
from buildbot.steps.http import HTTPStep
from buildbot.steps.source.git import Git
from requests.auth import HTTPBasicAuth
from twisted.logger import Logger

from steps.artifacts import Upload  # pylint: disable=relative-import


def replace_with_interpolate(obj):
    """Interpolate nested %(prop:obj)s in step arguments.

    Read step arguments from the yaml file and replaces them with
    interpolate objects when relevant so they can be replaced with
    properties when run.
    """

    if isinstance(obj, dict):
        return {k: replace_with_interpolate(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_with_interpolate(elem) for elem in obj]
    elif isinstance(obj, basestring) and 'prop:' in obj:
        return Interpolate(obj)
    else:
        return obj


def step_factory(custom_steps, step_type, **params):
    """Generate a buildbot step from dictionnary."""
    try:
        # try to see if the required step is imported or
        # defined in the current context
        _cls = custom_steps[step_type]
    except KeyError:
        # otherwise import the step from standars buildbot steps
        try:
            _cls = getattr(steps, step_type)
        except AttributeError:
            raise Exception('Could not load step %s' % step_type)

    # Replace the %(prop:*)s in the text with an Interpolate obj
    params = replace_with_interpolate(params)

    if issubclass(_cls, Git):
        # retry 10 times if git step fails, wait 60s between retries
        params['retry'] = (60, 10)

    if issubclass(_cls, Upload):
        # retry 5 times if upload step fails, wait 60s between retries
        params['retry'] = (60, 5)

    # hack to avoid putting clear passwords into the YAML file
    # for the HTTP step
    if issubclass(_cls, HTTPStep):
        pwd = params['auth'][1].replace('$', '')
        if pwd in environ:
            params['auth'] = HTTPBasicAuth(
                params['auth'][0], environ[pwd])

    # Hack! Buildbot does not accept unicode step names
    if 'name' in params and isinstance(params['name'], unicode):
        params['name'] = params['name'].encode('utf-8')

    return _cls(**params)


def define_local_job(job_conf_file, workers, suffix):
    # pylint: disable=too-many-locals
    """Add a single local job to eve config file."""
    logger = Logger('eve.common.define_local_job')

    with open(job_conf_file) as raw_conf:
        conf = yaml.load(raw_conf)
    default_name = path.split(job_conf_file)[-1]
    default_name = path.splitext(default_name)[0]

    factory = BuildFactory()

    logger.debug("creating a new build factory for local job %s" %
                 job_conf_file)
    for step in conf['steps']:
        step_type, params = next(step.iteritems())
        logger.debug("adding step %s with params: %s" % (step_type, params))
        factory.addStep(step_factory({}, step_type, **params))

    builder = conf.get('builder', {})
    builder_name = \
        builder.pop('name', '{0}{1}'.format(default_name, suffix))
    logger.debug("creating builder %s with params: %s" % (
        builder_name, builder))
    logger.debug("workers: %s" % [lw.name for lw in workers])
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
            'name', '{0}-scheduler{1}'.format(default_name, suffix))
    logger.debug("creating scheduler %s (%s) with params: %s" % (
        scheduler_name, _type, scheduler))
    scheduler = _cls(
        name=scheduler_name,
        builderNames=[builder_name],
        **scheduler
    )
    return builder, scheduler


def get_local_jobs(workers, suffix):
    """Load yaml local jobs in Eve config."""
    local_dirpath = path.join(
        path.dirname(__file__),
        environ.get('LOCAL_JOBS_DIRPATH', 'local'))
    builders = []
    scheds = []
    if path.isdir(local_dirpath):
        for job_conf_file in next(walk(local_dirpath))[2]:
            filename = path.join(local_dirpath, job_conf_file)
            try:
                blder, schdler = define_local_job(filename, workers, suffix)
                builders.append(blder)
                scheds.append(schdler)
            except Exception as error:
                raise Exception("There was an error while loading local job "
                                "%r, aborting (%s)" % (job_conf_file, error))
    return builders, scheds
