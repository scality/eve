Workers
=======

A worker is attached to each stage of a build. The worker is the physical
resource where the steps of the stage are executed. The resource can be of
different types: a simple shell in the local environment (local worker),
one or multiple containers (docker and pod workers), a virtual machine
(openstack worker).

It is important to understand that a worker is defined in the repository-under-test
itself, so that the developers of the CI can customize the tools and
dependencies required by the various steps of the stage.

In the build yaml file, for each stage, the worker is described in a mandatory
``worker`` section. The syntax of the section depends on the worker type,
and is described in each section below.

In order for the newly spawned workers to be able to communicate with Eve, each
worker instances are responsible for instanciating buildbot-worker, e.g. run::

    buildbot-worker create-worker . \
        "$BUILDMASTER:$BUILDMASTER_PORT" \
        "$WORKERNAME" "$WORKERPASS" \
     && buildbot-worker start --nodaemon

Eve guaranties that the four variables used in that command are passed to
the environment of the worker. **For some types of workers, Eve will run the
buildbot-worker automatically, for others it is the responsibility of the
worker definition in the repository to start it**. Check the worker
documentation below carefully.

Once the stage is complete, Eve will despawn the resources and ensure nothing
is left behind.

.. contents::
    :depth: 2
    :local:

Local worker
------------


A stage can run in the local context of Eve. This is sufficient for
very light stages that do not require any specific dependencies to
run (i.e. only very basic shell commands can be used in this type
of stage).

This worker type does not need any special configuration, and it is
not required for the developer to start buildbot-worker in this case.

.. _local_examples:

Examples
++++++++

.. code-block:: yaml
   :caption: local worker syntax

   stage_running_locally:
     worker:
       type: local
     steps:
       # ... describe very simple steps here

Docker worker
-------------


When a stage uses a worker of type ``docker``, Eve will spawn a container
corresponding to the specifications given in the parameters, and execute
the steps of that stage inside the container. Two types of images are
supported:

- **Dynamic images**

  When ``path`` is specified in the worker :ref:`docker_parameters`, Eve will
  automatically build the image defined in that directory, *before* the stage
  runs. Eve is expecting to find a valid Dockerfile and all files required for
  the docker build in ``path``. The resulting image is then used by Eve to
  spawn the container.

- **Static images**

  When :ref:`image <docker_images>` is specified in the worker :ref:`docker_parameters`, Eve
  expects the image is pre-built, and either present in the local docker
  registry, or available through an accessible remote registry. This image is
  then used to spawn the docker container.

The entrypoint of the container must be buildbot-worker, i.e. a line
like the following must appear in the Dockerfile::

    CMD buildbot-worker create-worker . \
        "$BUILDMASTER:$BUILDMASTER_PORT" \
        "$WORKERNAME" "$WORKERPASS" \
     && buildbot-worker start --nodaemon

.. _docker_examples:

Examples
++++++++

.. code-block:: yaml
   :caption: Build yaml with a stage running in a docker worker with a dynamic image

   stage_using_a_dynamically_built_image:
     worker:
       type: docker
       path: <path/to/docker/build/context:path>
       memory: <docker_max_memory:str>
       volumes:
         - </path/to/volume:path>
     steps:
       # ... describe steps here

.. code-block:: yaml
   :caption: Build yaml with a stage running in a docker worker with a pre-built image

   stage_using_a_prebuilt_image:
     worker:
       type: docker
       image: <name_of_image:str>
       memory: <docker_max_memory:str>
       volumes:
         - </path/to/volume:str>
     steps:
       # ... describe steps here

.. _docker_parameters:

Parameters
++++++++++

``path``
    A relative path pointing to a directory in the repository.
    The directory must be a valid Docker context, i.e. it
    must contain a Dockerfile and all files necessary to build
    the image. Just like a normal Docker context, links are
    not allowed.

    This parameter is ignored if ``image`` is specified.

``dockerfile``
    (optional): defaults to the ``Dockerfile`` located in ``path``.
    When specified, the argument will be the path to a ``Dockefile``
    that will be used in the build process. Note that it can be located
    either inside or outside the context.

.. _docker_images:

``image``
    The name of an image understandable by the ``docker run`` command.
    It can be an image in the local registry, or an image in a
    distant registry that is accessible to Eve.

``memory``
    (optional): defaults to maximum value authorized by Eve.
    The value set in this parameter is sent as-is to the docker run
    command. The value is however checked agains a maximum value that
    is authorized by Eve. Check the settings of Eve to obtain this
    maximum value.

``volumes``
    (optional): defaults to ``[]``.
    Volumes can be declared either in the Dockerfile directly, or
    in the parameters of the worker. The latter method is preferred,
    so that Eve can translate the volumes into Kubernetes equivalents,
    in the case when Eve runs on a Kubernetes cluster.

Openstack worker
----------------


When a stage uses a worker of type ``openstack``, Eve will spawn a single
virtual machine in the Openstack cloud configured for the project.

Eve automatically calls buildbot-worker for Openstack workers, there is no
need for the repository to do it (see start.sh below if you need to customize
this).

By default the username on the remote machine is ``eve``.

The virtual machine can be personnalized in two ways:

- **type of machine**

  It is mandatory to specify in the worker :ref:`openstack_parameters`, the
  name of the ``image name`` and ``flavor`` of the machine to boot in the
  Openstack instance. Check your cloud provider settings to identify valid
  values.

- **personalization of image and startup scripts**

  There are three customizable scripts that will run in order once the machine
  is up. Eve provides default scripts for each, which can be overwritten by
  the worker: place one or more scripts in the worker ``path``:

  - ``init.sh``,
  - ``start.sh``,
  - and ``requirements.sh``.

  ``init.sh <version>``

  Execute some shell commands to modify the setup of the VM (e.g.
  create the Buildbot user, install buildbot software, add extra users,
  start additional services, ...);
  This script takes one argument: the version of the Buildbot master.

  ``requirements.sh``

  Install extra packages on the worker; This script will be retried
  up to 5 times, so needs to be re-entrant.

  ``start.sh <master_fqdn> <master_port> <worker_name> <worker_password>``

  Create Builbot worker and start program buildbot-worker, like in the
  default sample below. This script takes four arguments: the master callback
  details and worker credentials.

.. code-block:: shell
   :caption: Default Openstack start script

   export LANG=en_US.utf8

   master_fqdn=$1
   master_port=$2
   worker_name=$3
   worker_password=$4

   sudo -iu eve buildbot-worker create-worker --umask=022 \
                                /home/eve/worker \
                                ${master_fqdn}:${master_port} \
                                ${worker_name} \
                                ${worker_password}

   sudo -iu eve buildbot-worker start /home/eve/worker


.. _openstack_examples:

Examples
++++++++

.. code-block:: yaml
   :caption: Openstack worker

   stage_running_on_a_virtal_machine:
     worker:
       type: openstack
       image: <image_name:str>
       flavor: <flavor_name:str>
       path: <path/to/worker/customisation:path>
     steps:
       # ... describe steps here

.. _openstack_parameters:

Parameters
++++++++++

``image``
    Name of image in the cloud provider.

    .. note::
      when a Red Hat image is set, eve will automatically register and
      unregister the image into the customer portal.

``flavor``
    iName of flavor in the cloud provider.

``path``
    (optional): defaults to ``<empty>``.
    If provided, ``path`` may contain two files to configure the worker:
    - init.sh
    - requirements.sh

Kubernetes pod worker
---------------------


When a stage uses a worker of type ``kube_pod``, Eve will spawn a pod
in the local Kubernetes cluster where Eve resides.

This type of worker is not activated by default. Check the settings of your
local Eve instance.

This worker provides a method to run multiple containers at the same time,
interacting with each other through the ``localhost`` interface inside the
pod. This is an extremely powerful method to run complex tests within a
rich environment.

The images provided in the :ref:`kube_parameters` are built by Eve
automatically before the stage runs.

As an option, it is possible to grant access to that worker to an external
Kubernetes cluster, if this Eve instance allows it. In that case, the pod
worker will be configured by Eve so that the pod can access the remote
cluster with the standard Kubernetes tooling (kubectl, helm, ...). To activate
this option, the pod :ref:`kube_parameters` must include a ``service`` section
that will describe what type of cluster is expected by the stage, and
the names of the namespaces that the stage will be allowed to access.

.. TODO add donstraints on pod definition
      eg must have requests for each pod

.. TODO Furthermore, the following will be added by eve to your pod definition

.. _kube_examples:

Examples
++++++++

.. _example_with_image_string_path:
.. code-block:: yaml
   :caption: A simple pod worker with two dynamic images

   stage_running_in_a_pod:
     worker:
       type: kube_pod
       path: <path/to/kubernetes/pod/definition:filepath>
       images:
         my_image: <path/to/image/context:path>
         my_other_image: <path/to/other/image/context:path>
       vars:
         <first_var:str>: <value:str,list,dict>
         <more_var:str>: <value:str,list,dict>
     steps:
       # ... describe steps here

.. _example_with_image_dict:
.. code-block:: yaml
   :caption: A pod worker with the dockerfile path different from the context

   stage_running_in_a_pod:
     worker:
       type: kube_pod
       path: <path/to/kubernetes/pod/definition:filepath>
       images:
         my_image:
           context: <path/to/image/context:path>
           dockerfile: <path/to/dockerfile:filepath>
         my_other_image: <path/to/other/image/context:path>
     steps:
       # ... describe steps here

.. code-block:: yaml
   :caption: A pod worker with access to an external cluster

   stage_running_in_a_pod:
     worker:
       type: kube_pod
       path: <path/to/kubernetes/pod/definition:filepath>
       images:
         <image:str>: <path/to/image/context:path>
       service:
         requests:
           version: <version_of_cluster:str>
           name: <name_of_cluster:str>
         namespaces:
           - <default_namespace:str>
           - <another_namespace:str>
     steps:
       # ... describe steps here

.. _kube_parameters:
.. code-block:: yaml
   :caption: Example of a Kubernetes pod yaml file with Eve

   apiVersion: v1
   kind: Pod
   metadata:
     name: "pod"
   spec:
     containers:
     - name: my-app
       resources:
         requests:
           cpu: 500m
           memory: 1Gi
         limits:
           cpu: "1"
           memory: 2Gi
       image: "{{ images.my_image }}"
       env:
       - name: CREDENTIALS
         value: '%(secret:credentials)s' # Note that you can also retrieve
                                         # secrets and properties inside a
                                         # worker yaml file
     - name: eve-worker
       resources:
         requests:
           cpu: 500m
           memory: 1Gi
         limits:
           cpu: "1"
           memory: 2Gi
       image: "{{ images.my_other_image }}"
       # Assuming you already have buildbot-worker installed on this image
       command:
         - /bin/sh
         - -c
         - >-
           buildbot-worker create-worker . ${BUILDMASTER}:${BUILDMASTER_PORT}
           ${WORKERNAME} ${WORKERPASS} && buildbot-worker start --nodaemon


Parameters
++++++++++

``path``
    The path to a valid kubernetes pod definiton file (yaml). This is
    the file that will be used to create the pod resource in the cluster.
    The file can be templated (jinja), in which case, the worker definition
    must contain a section ``vars`` with the values to use when the template
    is rendered.

``images``
    If the pod requires images that are defined in the repository, the path
    to the docker context must be specified in this dictionnary, where the
    keys are the images names (use as {{ images.key }} in the template), and
    the values are:

    - either a string pointing to the relative paths where the context
      (Dockerfile and files) is found in the repository (see example
      :ref:`example_with_image_string_path`),

    - or, a dictionnary which keys are ``context`` and ``dockerfile``, as in
      example :ref:`example_with_image_dict`:

        * ``context``
          a string pointing to the relative paths where the context
          is found in the repository,

        * ``dockerfile``
          (optional; default value: ``Dockerfile``)
          Defaults to the ``Dockerfile`` located in ``context``
          (docker build context path). When specified, the value will
          be the path to a ``Dockefile`` that will be used in the build
          process. Note that it can be located either inside or outside the
          context.

    - or, a mix of the previous two styles.


``vars``
    Dictionnary containing the templating data to render the pod file in
    ``path``.

``service``
    If absent, the pod will be created and cannot access any cluster.

    If present, Eve will configure access to an external Kubernetes
    cluster, so that the stage can run complex Kubernetes commands (e.g.
    deploying services, statefulsets, ...)

    Eve may provide more than one cluster; For example, there may be two
    clusters available for tests, one with version 1.9.2, and another with
    version 1.8.10. The stage can specify which cluster to select by adding
    a ``requests`` section to ``service``, and specify either the ``version``
    or the ``name`` of the cluster directly (see :ref:`kube_examples`).

    In order to prevent builds from interfering with each other in the test
    clusters, Eve may restrict access to a list of predefined namespaces
    for that stage. In this case, specify a list ``namespaces`` in ``service``.
    For example, if the stage requests a namespace ``myns``, the steps
    will be able to access the namespace "%(prop:myns)s" during the stage.
