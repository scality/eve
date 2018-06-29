Frequently asked questions
==========================

.. _how_to_force_build:

How to start a build on a branch manually?
------------------------------------------

On the UI main page select:
``builds`` -> ``builders`` -> ``bootstrap`` -> ``force`` -> enter your branch's name


Click on ``builds`` -> ``builders``:

.. image:: ../images/builders.png
   :target: ../_images/builders.png


Select the ``bootstrap``:

.. image:: ../images/bootstrap.png
   :target: ../_images/bootstrap.png

Click on the ``force`` bar on the up right :

.. image:: ../images/force-build.png
   :target: ../_images/force-build.png

Then fill up the ``form``:

.. image::  ../images/force-form.png
   :target: ../_images/force-form.png

Setup the branch name you want to build and click on ``Start Build``.

For an alternate way to start builds from your local command line,
check on :ref:`Eve command line tool <api_client>`.


How to build a commit hash?
---------------------------

Eve builds branches rather than commit hash. The reason is easy to understand
if you look at the mapping between branch names and stages to run at the
top of the yaml file.

Currently, eve refuses to build a commit that is not the tip of a branch (see
the :ref:`relevant automatic step <CancelNonTipBuild>`).

If you plan to build a commit that is the current tip of a branch, you can
follow the procedure described in :ref:`the section above
<how_to_force_build>`.

In order to build a commit that is not currently the tip of a branch, an
additional step is required: first create a branch pointing to the target
commit, and push it to the GIT server. Given the webhook settings on the
repository, the build will start automatically; alternatively, start a build
manually as described above.


Can builds be customised?
-------------------------

In the case of builds that are launched automatically (usually via a webhook
received when the repository is updated), Eve will always run the build with
the default values that are specified in the yaml file, in particular the
stage to run and default property values.

Those values can however be customized for builds that are started manually
(either a build launched via the :ref:`build form <how_to_force_build>`, or via
the :ref:`command line <api_client>`).

The build stage to run can be forced in the ``Override stage`` box. It can
be used to build a single stage or a stage that the target branch would
normally not run.

Properties can be overridden in the ``extra properties`` box.

The values can be overriden on the build form:

.. image::  ../images/force-form.png
   :target: ../_images/force-form.png


A form where the stage name and some properties are customized will
look like this:

+----------------------------------+-----------------------------------+
| Build form example                                                   |
+==================================+===================================+
| branch                           | ``feature/new-stuff``             |
+----------------------------------+-----------------------------------+
| stage                            | ``post-merge``                    |
+----------------------------------+-----------------------------------+
| properties name                  | ``my_property``                   |
+----------------------------------+-----------------------------------+
| properties value                 | ``the value of my_property``      |
+----------------------------------+-----------------------------------+

If the yaml specifies a value for ``my_property``, this value will be
ignored and the value specified in the form will be used instead.


Can I have access to the workers to investigate my failing step?
----------------------------------------------------------------

Please contact the administrator of Eve to obtain access to a specific worker.


Why do my build artifacts reference version '0.0.0'?
----------------------------------------------------

You need to implement a :ref:`product version script <get_product_version>` in
order to tell Eve the current version of the repository.
