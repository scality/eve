Properties Steps
================

Properties are a useful way of passing information between the stages
of a build.

The standard Buildbot steps `SetProperty`_ and `SetPropertyFromCommand`_
can be used in the build yaml:

.. code-block:: yaml

   - SetProperty:
       name: setup a property
       property: my_prop
       value: my_prop

   - SetPropertyFromCommand:
       name: set a property with the last tag
       property: last_tag
       command: git describe --abbrev=0 --tags

SetBootstrapProperty
--------------------

This step works like the buildbot standard step `SetProperty`_, but as the
name indicates, the property is set on the bootstrap build instead of the
current build.

The main purpose of this step is to set a property that can be queried easily
when the bootstrap id is known.

Parameters
++++++++++

``property``
    The name of the property.

``value``
    The value of the property.

Example
+++++++

.. code-block:: yaml

   - SetBootstrapProperty:
       name: my_prop
       value: my_value

SetBootstrapPropertyFromCommand
-------------------------------

This step does the same as SetBootstrapProperty, and like the standard
Buildbot `SetPropertyFromCommand`_, it can execute a ShellCommand and
set the output as a property on the bootstrap.

Parameters
++++++++++

``property``
    The name of the property.

``command``
    The shell command which output will be stored in the property
    (as a string).

Example
+++++++

.. code-block:: yaml

  - SetBootstrapPropertyFromCommand:
      name: set test link
      property: testlink
      command: cat test_link.txt


.. _SetProperty: http://docs.buildbot.net/latest/manual/cfg-buildsteps.html#setting-properties

.. _SetPropertyFromCommand: http://docs.buildbot.net/latest/manual/cfg-buildsteps.html#setpropertyfromcommand
