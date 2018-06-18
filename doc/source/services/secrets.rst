Secret manager
==============

When activated, this micro-service provides a secure access to secrets that have
been previously registered in the system. Eve uses vault as the backend
technology to secure the data. Eve will mask all occurences of the secrets in
logs and standard outputs of the steps of each build.

In order to register a new secret, ask an administrator to create a new entry
for you.  You will need to provide a key/value pair. In the project yaml, use
a property of type `secret` to get the value. The example below demonstrates
how to extract a `docker registry login` and a `docker registry password` from
the secrets and use those two secrets in a Docker login sequence:

.. code-block:: yaml
   :caption: eve/main.yml

   - ShellCommand:
       name: "login to private registry"
       command: >
           docker login
           --user %(secret:docker_registry_username)s
           --password %(secret:docker_registry_password)s
