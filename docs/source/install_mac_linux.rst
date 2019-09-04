Mac and Linux OS installation
=============================

1. Download the latest Miniconda3 installer from the `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ web page.

2. Run the installer setup locally (select the *Install for me only* on Mac/Linux) to avoid the need for administrator privileges.

3. Leave the default folder path (``/Users/<username>/miniconda3`` or ``/home/<username>/miniconda3``).

4. Do not add Anaconda to the PATH. Do, however, register Anaconda as the default Python environment.

5. Open up a Terminal. The ``base`` environment is being activated and the prompt changes to: ``(base)/Users/<username>`` or ``(base)/home/<username>``:

6. Create the python environment (``pyincore`` for example) and activate it (or stay in the ``base``):

    .. code-block:: bash

        conda create -n pyincore python=3
        conda activate pyincore

7. Add `conda-forge <https://conda-forge.org/>`_ package repository to your environment:

    .. code-block:: bash

        conda config --add channels conda-forge

8. Install Jupyter Notebook. Jupyter Notebook is already installed with Anaconda distribution; it has to be installed separately in your virtual environment on Miniconda:

    .. code-block:: bash

        conda install jupyter

Mac OS specific notes: We use ``matplotlib`` library to create graphs. There is a Mac specific installation issue addressed at StackOverflow `link 1 <https://stackoverflow.com/questions/4130355/python-matplotlib-framework-under-macosx>`_ and `link 2 <https://stackoverflow.com/questions/21784641/installation-issue-with-matplotlib-python>`_. In a nutshell, insert line:
    .. code-block:: bash

        backend : Agg

into ``~/.matplotlib/matplotlibrc`` file. You must create the file (``matplotlibrc``) if it does not exist.


----

`IN-CORE home <index.html>`_






