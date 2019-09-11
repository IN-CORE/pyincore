Windows 64-bit installation
===========================

1. Download the latest Miniconda3 installer for Windows from the `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ web page.

2. Run the installer setup locally (select the *Just Me* choice) to avoid the need for administrator privileges.

3. Leave the default folder path (``C:\Users\<user>\..\miniconda3``).

4. Do not add Anaconda to the PATH. Do, however, register Anaconda as the default Python environment.

5. Open up an Anaconda prompt from the Windows Start menu. The ``base`` environment is being activated and the prompt changes to: ``(base) C:\Users\<user>``:

    .. image:: images/win_prompt1.jpg
        :height: 324px
        :width: 346px
        :scale: 100 %
        :alt: Windows Menu
        :align: center

    |

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


----

`IN-CORE home <index.html>`_
