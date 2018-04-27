Build steps
===========

A CI build running on Eve can use all the standard build steps provided
by Buildbot. Additionally, Eve provides a number of customized steps that
are described in this documentation.

- The standard steps are described in `Buildbot's online documentation`_.
- The custom steps are described below.

Converting steps into yaml
--------------------------

The steps parameters translate directly into yaml entries in the build yaml
file. For example, the buildbot standard step `ShellCommand`_ supports the
following parameters according to Buildbot's documentation:

- name
- command
- workdir
- env
- want_stdout
- want_stderr
- usePTY
- logfiles
- ...

When specifying a `ShellCommand`_ in the build yaml, simply write:

.. code-block:: yaml

   - ShellCommand:
       name: Execute a shell command
       command: make all
       workdir: /home
       env:  # expects a dictionnary
         KEY1: value
         KEY2: value
       want_stdout: true
       # etc...

There is a correspondance between the type of the expected parameters
and the type of yaml to write (as per PyYAML translation):

- string parameter -> yaml string
- dictionnary parameter -> yaml dictionnary
- list parameter -> yaml list
- boolean parameter -> yaml true/false

Custom steps
------------

.. toctree::
   :caption: Contents:
   :name: reference_steps_page
   :maxdepth:   2

   steps/artifacts
   steps/test_reports
   steps/docker
   steps/property
   steps/build_lifecycle
   steps/misc


.. _Buildbot's online documentation: http://docs.buildbot.net/current/manual/cfg-buildsteps.html

.. _ShellCommand: http://docs.buildbot.net/latest/manual/cfg-buildsteps.html#shellcommand
