# pyincore

**pyIncore** is a Python project to analyze and visualize various hazard (earthquake, tornado, hurricane etc.) 
scenarios developed by the Center for Risk-Based Community Resilience Planning team from NCSA. 
The development is part of NIST sponsored IN-CORE (Interdependent Networked Community Resilience Modeling 
Environment) initiative. pyIncore allows users to apply hazards on infrastructure in selected areas. 
Python framework accesses underlying data through local or remote services and facilitates moving 
and synthesizing results.
                      
**pyincore** as a Python module can be used to write hazard workflow tools. We envision users writing tools 
as a [Jupyter](https://jupyter.org/) notebooks.

### Prerequisites

A user must have an account recognized by the **IN-CORE** service. Please [register](https://identity.ncsa.illinois.edu/register/UUMK36FU2M) and use your credentials later on.

[Python 3.5](https://www.python.org) or greater

[GDAL](https://www.gdal.org) - Geospatial Data Abstraction Library

- **Linux** 

    **Pyincore** uses GDAL library which has to be installed separately for example by using `apt-get` package utility 
    on Debian, Ubuntu, and related Linux distributions.
    ```
    apt-get gdal
    ```
    Additional information can be found  at the wiki page [How to install GDAL](https://github.com/domlysz/BlenderGIS/wiki/How-to-install-GDAL).

- **Windows**

    GDAL for Windows can be difficult to build, requiring a number of prerequisite software, libraries, and header files. 
    If you are comfortable building Windows software then building GDAL from source as a develop build is preferred.
    
    If you are not comfortable building GDAL then you may want to download the `gdal` binaries 
    from [Windows Binaries for Python](https://www.lfd.uci.edu/~gohlke/pythonlibs/). 
    The problem with this is that GDAL header files are not included, so you cannot do a `pip install` of packages that want to utilize 
    the GDAL headers. Fiona and Rasterio will need binaries installed from this page as well, 
    and if you run into failed dependencies during the setup process you may want to revisit 
    the page and install the binaries for the Python extensions that are causing problems. 
    Additional information can be found at the wiki page [How to install GDAL](https://github.com/domlysz/BlenderGIS/wiki/How-to-install-GDAL).


**Optional**: A [virtual environment](https://www.pythonforbeginners.com/basics/how-to-use-python-virtualenv/), a tool that helps to keep dependencies required by different projects separate
by creating isolated Python virtual environments for them. A module named `virtualenv` is available by running `pip3 install virtualenv` 
(`pip3` command is pip for Python3, you could also run `pip3 install --upgrade pip` first), or an environment manager 
called [Anaconda](https://www.anaconda.com/distribution/) by downloading OS specific [installer](https://docs.anaconda.com/anaconda/install/).

Note that a full Anaconda distribution will include Python (and a collection of over 1,500+ open source packages), so installing Python first isn't needed if you use Anaconda.

[Jupyter notebook](https://jupyter.org/) - We recommend using Jupyter notebook for running the **pyIncore** projects. 
It as an open-source application that allows you to create projects (documents) that contain live Python code, 
visualizations and documentation. [Installing Jupyter](https://jupyter.org/install.html) can be done again with pip by 
running `pip3 install jupyter`. With **Anaconda** you already have installed Jupyter notebook.


## Installation

### All Platforms

We envision a user developing project (in Jupyter notebooks) in his or her Project folder which is separated from the pyincore package folder. 
Both should run within the same Python virtual environment.

1. Download **pyincore** as an archive file from [NCSA's server](https://incore2.ncsa.illinois.edu/releases/pyincore_0.2.0.tar.gz) to a directory on your computer.
2. **Optional**: Activate your virtual (`source virtual_env_name/bin/activate`) or conda (`source activate virtual_env_name`) environment 
from the folder you downloaded the pyincore package to. The conda is the preferred interface for managing installations and virtual environments with the Anaconda Python distribution. 
The conda is the preferred interface for managing installations and virtual environments with the Anaconda Python distribution. The name of the current virtual environment 
will now appear in round brackets on the left of the prompt (e.g. `(venv) computer_name:folder username$`) to let you know that it is active.
3. From the terminal run:
    ```
    pip3 install --user pyincore_0.2.0.tar.gz
    ```
    
    The installation creates a folder called `pyincore` which is a pyIncore directory, and `.incore` folder in your HOME directory. 
    A message *pyIncore credentials file has been created at <HOME directory>/.incore/.incorepw* appears in the terminal/prompt. 
    The typical location of a HOME directory is `C:\Users\<username>` on Windows OS, `/Users/<username>` on MacOS 
    and `/home/<username>` on Linux based machines.

**Windows specific installation notes**
    
- Open the `Anaconda` prompt, or `cmd` depending on if you are using Anaconda or not before you activate 
virtual environment (step 2 above)

**Mac specific installation notes**

- `spacialindex` library is needed, but appears to be included on other platforms. The easy way to install 
is to use [Homebrew](https://brew.sh/), and run:
    ```
    brew install spacialindex
    ```
    
- We use `matplotlib` library to create graphs. There is a Mac specific installation issue addressed at 
StackOverflow [link1](https://stackoverflow.com/questions/4130355/python-matplotlib-framework-under-macosx) and 
[link2](https://stackoverflow.com/questions/21784641/installation-issue-with-matplotlib-python). In a nutshell, 
insert line:
    ```
    backend : Agg
    ```

    into `~/.matplotlib/matplotlibrc` file.

## Running

- Locate a file called `.incorepw` and write your credentials in it; the first line contains your username and the second password. 
The information is used for communicating with **IN-CORE** services such as hazard, data and fragility. 
The file is located in the `.incore` folder created during installation in a user's HOME directory. The typical path is `C:\Users\<username>` on Windows OS, 
`/Users/<username>` on MacOS and `/home/<username>` on Linux based machines.

- Start local Jupyter notebook by running the following command at the Terminal (Mac/Linux) or Command Prompt (Windows) **from a Project folder**:
    ```
    jupyter notebook
    ```
    
    Again, the name of the current virtual environment could appear in round brackets on the left of the prompt. 
    
    A message *The Jupyter Notebook is running* appears in the terminal/prompt 
    and you should see the notebook open in your browser. 
    Note that you will be asked to copy/paste a token into your browser when you connect 
    for the first time.


- Download the **Building damage analysis** Jupyter notebook ([`buildingdamage.ipynb`]((http://incore2.ncsa.illinois.edu/doc/examples/buildingdamage.ipynb))) 
and verify the installation by running it from your project folder. For details of running and manipulating `ipynb` files refer 
to [Jupyter documentation](https://jupyter.readthedocs.io/en/latest/running.html#running).


Additionally, a user can run Jupyter notebook interactively in NCSA's [IN-CORE Lab](https://incore-jupyter.ncsa.illinois.edu/hub/login).


## Documentation

**Pyincore** documentation can be found on [IN-CORE server](http://incore2.ncsa.illinois.edu/).


## Acknowledgement
This work was performed under financial assistance award 70NANB15H044 from 
the National Institute of Standards and Technology (NIST) as part of 
the Interdependent Networked Community Resilience Modeling 
Environment [(IN-CORE)](http://resilience.colostate.edu/in_core.shtml).