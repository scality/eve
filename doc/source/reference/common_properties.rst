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
