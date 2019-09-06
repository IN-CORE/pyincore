pyIncore installation
=====================

- **pyIncore package**

    These steps will guide you on how to install **pyIncore**.

    1. To install pyIncore, navigate to the directory you want to use for running Jupyter Notebooks and run the following command (single line command):

        .. code-block:: bash

            conda install -c https://inconda:CHANNEL_PWD_HERE@incore2.ncsa.illinois.edu/conda/pyincore/ pyincore


       Contact us at ``incore-dev@lists.illinois.edu`` for details of **channel password** (CHANNEL_PWD_HERE is a placeholder for the real password). This command tells conda to install the ``pyincore`` package from the NCSA's conda ``incore`` channel.

    An alternative approach is to register conda channel in ``.condarc`` file which contains names and url links of the channels. The file is usually stored in your HOME directory. The typical location of a HOME directory is ``C:\Users\<username>\`` on Windows OS, ``/Users/<username>`` on Mac OS and ``/home/<username>/`` on Linux based machines.

    1.	Add NCSA’s **pyincore** package repository, conda channel to your environment (single line command without spaces):

        .. code-block:: bash

            conda config --append channels https://inconda:CHANNEL_PWD_HERE@incore2.ncsa.illinois.edu/conda/pyincore/


    2.	To install **pyIncore**, navigate to the directory you want to use for running Jupyter Notebooks and run the following command:

        .. code-block:: bash

            conda install pyincore


    To check that the package is installed run ``conda list command``.

    Replace ``install`` command above with ``update`` to update **pyincore** to the latest version that is compatible with all other packages in the environment.



- **pyIncore credentials**

    The installation installs **pyIncore** and creates ``.incore`` folder in your HOME directory to store cached files. A message *pyIncore credentials file has been created at <HOME directory>/.incore/.incorepw appears* in the prompt. The typical location of a HOME directory is ``C:\Users\<username>\`` on Windows OS, ``/Users/<username>`` on Mac OS and ``/home/<username>/`` on Linux based machines.

    **Note**: The folders and files starting with "." (dot prefix) are hidden in Operating systems with Unix roots. There are few ways (`link1 <https://nektony.com/how-to/show-hidden-files-on-mac>`_ and `link2 <https://macpaw.com/how-to/show-hidden-files-on-mac>`_) to view hidden files on your Mac.


    1. Locate a file called ``.incorepw`` in the ``.incore`` folder in your HOME directory.
    2. Write your LDAP credentials in it; the first line contains your **username** and the second **password**. This information is used for communicating with IN-CORE web service.


----

`IN-CORE home <index.html>`_
