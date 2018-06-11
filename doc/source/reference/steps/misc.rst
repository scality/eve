Misc steps
==========

Here are the commands that don't fit in any other category.

ShellCommandWithSecrets
-----------------------

Execute a shell command that needs access to secret environment variables.

All variables on the form ``SECRET_{var}`` will be passed as ``{var}`` inside the
worker. The environment is **not** logged during such a step.

Parameters
++++++++++

See `ShellCommand`_

Example
+++++++

.. code-block:: yaml

   - ShellCommandWithSecrets:
       name: Deployment with secrets
       command: make deploy
       maxTime: 300
       haltOnFailure: True

.. _ShellCommand: http://docs.buildbot.net/latest/manual/cfg-buildsteps.html#shellcommand
