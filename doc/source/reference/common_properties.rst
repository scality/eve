.. _properties:

Common properties
=================

Before starting the builds eve will implicitly set properties that can be
used with the following syntax: ``%(prop:my_property)s``.
Users can also set their own properties with the ``SetProperty`` step or
even ``SetPropertyFromCommand``.

``bootstrap``
    Number of the bootstrap build that triggered the stage (i.e.
    master build id).

``bootstrap_reason``
    A string showing the reason for the build. Default values are: "force build"
    and "branch updated". When the force build form or the API are used to
    trigger a build, the reason string can be customised.

``branch``
    The branch that is being built.

``conf``
    This property contains the yaml that triggered the build (i.e. eve/main.yml)

``eve_api_version``
    Version of the yaml in the repository.

``max_step_duration``
    Shows the max duration of a step, as setup in Eve configuration. Steps lasting
    longer than this value will be killed by Eve.

``stage_name``
    The name of the current stage.

``worker_uuid``
    A md5 sum hash that will be created for you. This property can be useful
    when a build spawns its own resources with specific scripts or tools.

    .. warning::
      The ``worker_uuid`` is unique enough so that it doesn't conflict with
      stages running in the same build or different one. They're generated
      from the buildbot worker name and the repository name.

``simultaneous_builds``
    Can be set at the the stage level, and this setting allows the user to control
    the number of consecutive builds that can run at the same time. Per example it
    it is useful for deployments to allow only one build at the time to run.

    Usage:

    .. code-block:: yaml

        stages:
          pre-merge:
            # in this case only one build is allowed
            simultaneous_builds: 1
            worker:
            # worker specs
            # ...
            steps:
            # steps specs
            # ..
