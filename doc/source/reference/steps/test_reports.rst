Test reports handling
=====================

Steps snooping on test results.

JUnitShellCommand
-----------------

A `ShellCommand`_ that sniffs junit output.

Can give you the ability to fail if a shell command succeed but you need to
check a JUnit report to ensure that all tests succeeded.

Parameters
++++++++++

This step inherits from `ShellCommand`_ so it will work almost the same, but will
add two new parameters.

``report_dir``
    The directory where the JUnit report is looked for.

``report_path``
    The file full paths where the JUnit reports are.

Please note, those two parameters are mutually exclusive. Also, ``report_path``
is preferred to ``report_dir`` for performance reasons.

Examples
++++++++

.. code-block:: yaml

    - JUnitShellCommand:
        report_dir: build/tests/reports
        name: execute tests
        command: make test
        haltOnFailure: True

.. code-block:: yaml

    - JUnitShellCommand:
        report_path: build/tests/reports/output*.xml
        name: execute tests
        command: make test
        haltOnFailure: True

.. code-block:: yaml

    - JUnitShellCommand:
        report_path:
          - build/tests/reports/output1.xml
          - build/tests/reports/output2.xml
        name: execute tests
        command: make test
        haltOnFailure: True

.. _ShellCommand: http://docs.buildbot.net/latest/manual/cfg-buildsteps.html#shellcommand

PublishCoverageReport
---------------------

Parameters
++++++++++

``repository``
    Name of the git repository.

``revision``
    The destination commit sha for the report.

``filepaths``
    List of code coverage report file path.

``branch``
    (optional)
    Name of the branch.

``uploadName``
    (optional)
    Upload identifier.

``flags``
    (optional)
    List of report flag.

``configFile``
    (optional)
    Codecov config file.

``skipMissingFile``
    (optional)
    Skip or not missing report file.

``maxSize``
    (optional)
    Upload max size.

``blockSize``
    (optional)
    Upload block size.

Example
+++++++

.. code-block:: yaml

   - PublishCoverageReport:
       repository: "%(prop:git_owner)s/%(prop:git_slug)s"
       revision: "%(prop:revision)s"
       branch: "%(prop:branch)s"
       filepaths:
         - "build/tests/reports/last/coverage.xml"
       uploadName: "myreport"
       flags:
         - "unit"
       skipMissingFile: True
       configFile: ".codecov.yml"
       haltOnFailure: False
       flunkOnFailure: False
