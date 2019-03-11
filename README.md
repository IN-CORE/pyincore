# pyincore

**pyIncore** is a Python project to analyze and visualize various hazard (earthquake, tornado, hurricane etc.) 
scenarios developed by the Center for Risk-Based Community Resilience Planning team from NCSA. 
The development is part of NIST sponsored IN-CORE (Interdependent Networked Community Resilience Modeling 
Environment) initiative. pyIncore allows users to apply hazards on infrastructure in selected areas. 
Python framework accesses underlying data through local or remote services and facilitates moving 
and synthesizing results.
                      
**pyincore** as a Python module can be used to write hazard workflow tools. We envision users writing tools 
as [Jupyter](https://jupyter.org/) notebooks.

### Prerequisites

A user must have an account recognized by the **IN-CORE** service. Please [register](https://identity.ncsa.illinois.edu/register/UUMK36FU2M) 
since your credentials will be required in later steps.

[Python 3.5+](https://www.python.org) or greater

[GDAL](https://www.gdal.org) - Geospatial Data Abstraction Library

- **Linux** 

    **Pyincore** uses GDAL library which has to be installed separately for example by using `apt-get` package utility 
    on Debian, Ubuntu, and related Linux distributions.
    ```
    sudo apt-get install gdal-bin
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

- **MacOS**
    The easiest way is to use [Homebrew](https://brew.sh/), a MacOS package manager.
    - Follow the instructions to install Homebrew.
    - [Install](https://medium.com/@vascofernandes_13322/how-to-install-gdal-on-macos-6a76fb5e24a4) the current version of gdal:
    ```
    brew install gdal
    ```
    - Update the `pip` Python package manager and finally install GDAL for Python:
    ```
    pip3 install --upgrade pip
    pip3 install gdal
    ```
    
[Jupyter notebook](https://jupyter.org/) - We recommend using Jupyter notebook for running the **pyIncore** projects. 
It as an open-source application that allows you to create projects (documents) that contain live Python code, 
visualizations and documentation. [Installing Jupyter](https://jupyter.org/install.html) can be done again with pip by 
running `pip3 install jupyter`.

**Optional**: We recommend to use [virtual](https://www.pythonforbeginners.com/basics/how-to-use-python-virtualenv/) environment 
or environment [manager](https://www.anaconda.com/distribution/); tools that help keep dependencies separate for different projects.

## Installation

### All Platforms

We envision a user developing their project in a Jupyter notebook in his or her **Project folder**. 
These steps will guide you on how to install both pyIncore and Jupyter notebook so you can develop your code.

1. Download **pyincore** as an archive file from [NCSA's server](https://incore2.ncsa.illinois.edu/releases/pyincore_0.2.0.tar.gz) to a directory on your computer.
2. From the Terminal (Mac/Linux) or Command Prompt (Windows) run:
    ```
    pip3 install --user pyincore_0.2.0.tar.gz
    ```
    
    The installation installs pyIncore and creates a `.incore` folder in your HOME directory to store cached files. 
    A message *pyIncore credentials file has been created at <HOME directory>/.incore/.incorepw* appears 
    in the terminal/prompt. The typical location of a HOME directory is `C:\Users\<username>` on Windows OS, `/Users/<username>` on MacOS 
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
The file is located in the `.incore` folder created during installation in your HOME directory. The typical path is `C:\Users\<username>` on Windows OS, 
`/Users/<username>` on MacOS and `/home/<username>` on Linux based machines.

- Start local **Jupyter notebook** by running the following command at the terminal or command prompt from a **Project folder**:
    ```
    jupyter notebook
    ```
       
    A message *The Jupyter Notebook is running* appears in the terminal/prompt 
    and you should see the notebook open in your browser. 
    Note that you will be asked to copy/paste a token into your browser when you connect 
    for the first time.


- Download the **Building damage analysis** Jupyter notebook (<http://incore2.ncsa.illinois.edu/doc/examples/buildingdamage.ipynb>) 
and verify the installation by running it from your project folder. For details of running and manipulating `ipynb` files refer 
to [Jupyter documentation](https://jupyter.readthedocs.io/en/latest/running.html#running). If you have problems running notebooks, 
contact us at **incore-dev@lists.illinois.edu**.


Additionally, a user can run Jupyter notebook interactively in NCSA's [IN-CORE Lab](https://incore-jupyter.ncsa.illinois.edu/hub/login). (*coming soon*)


## Documentation

**pyIncore** documentation can be found on [IN-CORE server](http://incore2.ncsa.illinois.edu/).


## Acknowledgement
This work was performed under financial assistance award 70NANB15H044 from 
the National Institute of Standards and Technology (NIST) as part of 
the Interdependent Networked Community Resilience Modeling 
Environment [(IN-CORE)](http://resilience.colostate.edu/in_core.shtml).