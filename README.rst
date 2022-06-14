pyincore
========

**pyIncore** is a component of IN-CORE. It is a python package
consisting of three primary components: 1) a set of service classes to
interact with the IN-CORE web services described below, 2) IN-CORE
analyses and 3) visualization. The pyIncore allows users to apply
various hazards to infrastructure in selected areas, propagating the
effect of physical infrastructure damage and loss of functionality to
social and economic impacts.

Prerequisites
-------------

-  Requirements: IN-CORE account, Python 3.6-3.8, Anaconda or Miniconda,
   Jupyter notebook.

Please read through the
`Prerequisites <https://incore.ncsa.illinois.edu/doc/incore/pyincore/prerequisites.html>`__
section at IN-CORE manual at least once completely before actually
following them to avoid any installation problems!

Installation
------------

You can find this information at the
`Installation <https://incore.ncsa.illinois.edu/doc/incore/pyincore/install_pyincore.html>`__
section at IN-CORE manual.

1. From the Terminal (Mac/Linux) or Command Prompt (Windows) add
   `conda-forge <https://conda-forge.org/>`__ package repository/channel
   to your environment: ``conda config –-add channels conda-forge``

2. To install pyIncore, navigate to the directory you want to use for
   running Jupyter Notebooks and run the following command:
   ``conda install -c in-core pyincore``

To check that the package is installed. run

::

   conda list

It will list all packages currently installed. You can check if pyincore
exists in the list.

To update pyIncore run

::

   conda update -c in-core pyincore

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
