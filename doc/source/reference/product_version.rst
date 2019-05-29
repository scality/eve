.. _get_product_version:

Product version
===============

You can instruct Eve what version of the repository is being tested by adding
a file named ``get_product_version.sh`` in the same directory that contains
the yaml CI definition file (by default: eve/get_product_version.sh).

The file ``get_product_version.sh`` must:

- be executable,
- return a string representing the version of the product/repository on that
  branch.
- the string must contain 2 to 4 numbers separated by a dot, and nothing else.

If the script is not present, Eve will consider the product version is
``0.0.0``

A property ``product_version`` is also set on the build with the value
returned by the script.
