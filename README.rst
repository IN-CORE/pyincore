pyincore
========

**pyIncore** is a component of IN-CORE. It is a python package
consisting of two primary components: 1) a set of service classes to
interact with the IN-CORE web services described below, and 2) IN-CORE
analyses. The pyIncore allows users to apply various hazards to infrastructure 
in selected areas, propagating the effect of physical infrastructure damage 
and loss of functionality to social and economic impacts.

Installation with conda
-----------------------

Installing **pyincore** with Conda is officially supported by IN-CORE development team. 

To add `conda-forge <https://conda-forge.org/>`__  channel to your environment, run

.. code-block:: console

   conda config –-add channels conda-forge

To install **pyincore** package, run

.. code-block:: console

   conda install -c in-core pyincore


To update **pyIncore**, run

.. code-block:: console

   conda update -c in-core pyincore

You can find detail information at the
`Installation <https://incore.ncsa.illinois.edu/doc/incore/pyincore/install_pyincore.html>`__
section at IN-CORE manual.

Installation with pip
-----------------------

Installing **pyincore** with pip is **NOT supported** by IN-CORE development team.
Please use pip for installing pyincore at your discretion. 

**Installing pyincore with pip is only tested on linux environment.**

**Prerequisite**

* GDAL C library must be installed to install pyincore. (for Ubuntu, **gdal-bin** and **libgdal-dev**)
* ipopt executable must be installed to run some analyses such as seaside CGE, joplin CGE, etc.
* For developers, pre-install must be installed. If not, run `brew install pre-commit` or `pip install pre-commit`.

To install **pyincore** package, run

.. code-block:: console

   pip install pyincore


Testing and Running
-------------------

Please read the `Testing and
Running <https://incore.ncsa.illinois.edu/doc/incore/pyincore/running.html>`__
section at IN-CORE manual.

Documentation
-------------

**pyIncore** documentation can be found at
https://incore.ncsa.illinois.edu/doc/incore/pyincore.html

**pyIncore** technical reference (API) can be found at
https://incore.ncsa.illinois.edu/doc/pyincore/.

Acknowledgement
---------------

This work herein was supported by the National Institute of Standards
and Technology (NIST) (Award No. 70NANB15H044). This support is
gratefully acknowledged. The views expressed in this work are those of
the authors and do not necessarily reflect the views of NIST.
