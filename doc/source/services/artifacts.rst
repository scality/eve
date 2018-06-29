Build artifacts
===============

Your builds generate a lot of data that you'll want to keep:

   * Test reports

   * Core dumps

   * binaries

   * packages

   * ...

Eve can keep your artifacts for 14 days if your commit is not promoted and
forever if the commit is promoted.

Artifacts are available for download from a web browser (see screenshots).

.. image:: ../images/artifacts-ui.png
   :target: ../_images/artifacts-ui.png


Create and upload artifacts
---------------------------

To upload an artifact, store all the files you want to upload in a single
directory (e.g. artifacts/).
Then add an Upload step and give it the name of the folder, like below:

.. code-block:: yaml
   :caption: eve/main.yml

   - ShellCommand:
       name: "prepare artifacts to be uploaded"
       command: >
           mkdir -p artifacts/repo artifacts/installer
           && cd artifacts/repo
           && ln -s `echo ../../build/prod/packages/repository/[0-9]*` %(prop:os_name)s
           && cd ../../artifacts/installer
           && ln -s `echo ../../build/prod/installer/installer*.run` .
       haltOnFailure: True
       alwaysRun: True
   - Upload:
       source: artifacts
       urls:
         - ['\1.run', 'installer/*.run']
       alwaysRun: True


Related build properties
------------------------

The property ``%(prop:artifacts_private_url)s`` can be used by other steps to
access, password free, a local and cached copy of artifacts already produced.

The property ``%(prop:artifacts_public_url)s`` will contain the URL of the
uploaded content for users outside the CI.

The property ``%(prop:product_version)s`` contains the version string of
the product, as returned by :ref:`the product version script
<get_product_version>`, if installed, ``0.0.0`` otherwise. This version
is printed in the artifacts bucket name.
