Build lifecycle
===============

This collection of steps are used by Eve internally to control when a build
should run, should be cancelled early, or how to sequence the steps, how to
parse the build yaml.

It is not recommended to use those steps in the build yaml, however, they
will appear in the steps of each build nevertheless (inserted by Eve).

CancelCommand
-------------

Cancel a build according to the result of the command provided in parameters.

Used internally by Eve. Do not use in the build yaml.

CancelNonTipBuild
-----------------

Cancel the build if the current revision is not the tip of the branch.

Used internally by Eve. Do not use in the build yaml.

This step is implicitely set by Eve on every builds. It prevents Eve from
executing useless/old builds.

CancelOldBuild
--------------

Cancel the build if the buildrequest has been created by a previous instance
of Eve/Buildbot.

Used internally by Eve. Do not use in the build yaml.

This step is implicitely set by Eve on every builds. It prevent Eve from
executing a build which was requested before an upgrade of the CI.

TriggerStages
-------------

Start a list of stages.

Parameters:

``stage_names``
    A list of stages that will be triggered simultaneously.

Example:

.. code-block:: yaml

    stages:
      pre-merge:
        worker:
          type: docker
          path: eve/workers/trusty
        steps:
          - TriggerStages:
              name: static checks and test stages simultaneously
              stage_names:
                - static checks
                - system tests
      static checks:
        worker:
          type: docker
          path: eve/workers/trusty
        steps:
          ...
      system tests:
        worker:
          type: docker
          path: eve/workers/trusty
        steps:
          ...


ExecuteTriggerStages
--------------------

Execute simultaneously multiple build steps.

It's a fake Trigger stage which run multiple BuildStep simultaneously.

.. TODO how does it work? I'm not seeing this step in any build yaml. 

ReadConfFromYaml
----------------

This step is used internally by eve. You will never use it in your build yaml.

Load the YAML file to ``conf`` property.

This step Reads the YAML file and converts it to a `conf` property which
is made available to the following steps.

StepExtractor
-------------

This step is used internally by Eve.

Extract and add the build steps to the current builder.

This step extracts the build steps from the ``conf`` property and adds them
to the current builder. It also adds a step to build an image.

GetCommitShortVersion
---------------------

Get the commit short version of the current branch.

This step is set internally by Eve, you do not need to declare it in your build
yaml, the property can be used with the following syntax
``%(prop:commit_short_revision)``.

GetCommitTimestamp
------------------

Get the commit timestamp and set a property ``commit_timestamp`` on the build.

This step is set internally by Eve, you do not need to declare it in your build yaml,
the property can be used with the following syntax
``%(prop:commit_timestamp)s``.

GetApiVersion
-------------

This step is used internally by Eve.

Get the build yaml API version and set a property ``eve_api_version`` on the
build.

PatcherConfig
-------------

This step is used internally by Eve to evaluate the system level skips. It
runs implicitely for each build, and will prevent the build from running if
the criterias to skip are met.

The patcher allows the administrator of Eve to cancel the execution of
specific stages, steps, or branches.

The patcher is useful to temporarily deactivate a step that may be temporarily
broken, like a missing external dependency for example.

The patcher is also useful on development environments, when stages can affect
the production:

* Avoid uploading test results into an external service,
* Avoid uploading artifacts,
* Avoid continuous delivery to be triggered involuntarily.
