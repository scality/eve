Docker images
=============

Steps designed to execute docker commands.

DockerBuild
-----------

Build a docker image.

Parameters
++++++++++

``label``
    The reference name of the image (for display in UI).

``image``
    The full repo:name:tag of the image to build.

``context_dir``
    Full path to the docker context. Equivalent to the path parameter given to
    a ``docker build`` command.

``dockerfile``
    (optional; default value: ``Dockerfile``)
    Defaults to the ``Dockerfile`` located in ``context_dir``
    (docker build context path). When specified, the argument will
    be the path to a ``Dockefile`` that will be used in the build
    process. Note that it can be located either inside or outside the
    context.

``is_retry``
    (optional; default value: ``False``)
    Set to True if this step was already tried before.

``labels``
    (optional; default value: ``[]``)
    Add additionnal label to the image.

``build_args``
    (optional; default value: ``[]``)
    Provide additional ``--build-args`` to the ``docker build`` command.

Example
+++++++

.. code-block:: yaml

   - DockerBuild:
       label: my_image
       context_dir: path/to/context/dir
       image: scality/my_image:latest
       dockerfile: path/to/dockerfile # optional

DockerCheckLocalImage
---------------------

Check for existence of a Docker image locally.

Look up the fingerprint of given image in local images, and sets
the ``exists_[label]`` property either to ``True`` or ``False``.

Parameters
++++++++++

``label``
    The reference name of the image (for display in UI and property).

``image``
    The full repo:name:tag of the image to look up.

Example
+++++++

.. code-block:: yaml

   - DockerCheckLocalImage:
       label: my_image
       image: scality:my_image:latest

DockerComputeImageFingerprint
-----------------------------

Compute the fingerprint of a docker context.

This step computes the sha256 fingerprint of an image given its context and
stores it to the property ``fingerprint_[label]``.

Parameters
++++++++++

``label``
    The reference name of the image (for display in UI and property).

``context_dir``
    Full path to the context directory.

Example
+++++++

.. code-block:: yaml

   - DockerComputeImageFingerprint:
       label: my_image
       context_dir: path/to/my/context

DockerPull
----------

Pull an image from a registry.

This step attempts to pull an image from a registry referenced in the
provided image name itself, and stores the result (True or False) to
the property ``exists_[label]``.

Parameters
++++++++++

``label``
    The reference name of the image (for display in UI and property).

``image``
    The full repo:name:tag of the image to look up.

Example
+++++++

.. code-block:: yaml

   - DockerPull:
       label: my_image
       image: scality/my_image:latest

DockerPush
----------

Push a Docker image to the custom registry.

This step attempts to push an image to a registry referenced in the
provided image name itself.

Parameters
++++++++++

``label``
    The reference name of the image (for display in UI).

``image``
    The full repo:name:tag of the image to look up.

Example
+++++++

.. code-block:: yaml

   - DockerPush:
       label: my_image
       image: scality/my_image:latest
