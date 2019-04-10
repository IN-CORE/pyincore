# pyincore

**pyIncore** is a Python project to analyze and visualize various hazard (earthquake, tornado, hurricane etc.) 
scenarios developed by the Center for Risk-Based Community Resilience Planning team from NCSA. 
The development is part of NIST sponsored IN-CORE (Interdependent Networked Community Resilience Modeling 
Environment) initiative. pyIncore allows users to apply hazards on infrastructure in selected areas. 
Python framework accesses underlying data through local or remote services and facilitates moving and synthesizing 
results.
                      
**pyincore** as a Python module can be used to develop scientific analysis/algorithm.

### Prerequisites

**IN-CORE account**

- A user must have an account recognized by the **IN-CORE** service. Please [register](https://identity.ncsa.illinois.edu/register/UUMK36FU2M) 
since your credentials will be required in later steps.

[Python 3.5+](https://www.python.org)

[GDAL](https://www.gdal.org) - Geospatial Data Abstraction Library
    
- **pyIncore** uses `GDAL` library, which has to be installed separately.

- **Linux** 
    - Install **gdal-bin**. Additional information can be found  at the wiki page [How to install GDAL](https://github.com/domlysz/BlenderGIS/wiki/How-to-install-GDAL).
        ```
        sudo apt-get install gdal-bin
        ```
    - Install **libspatialindex-dev**
        ```
        apt-get install libspatialindex-dev
        ```

- **Windows 64bit**
    The following instruction is tested for Win 64bit. But 32bit has not been tested yet.
    - Download the `GDAL` binaries for Win 64bit (`GDAL-2.3.3`) from [Windows Binaries for Python](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal) and install it using pip
        ```
        pip3 install <path-to-local-gdal-binary-whl-file>
        ```
        Note that GDAL header files are not included, so you cannot install dependencies through the pyincore setup process, 
        so you cannot install dependencies through the pyincore setup process. The binary files for the dependent packages 
        have to be pre-installed as well. 
    - Download each library below separately for your Python version. For example, if your Python version is 3.7, 
    you would download files that have `cp37-win_amd64` from the [link above](https://www.lfd.uci.edu/~gohlke/pythonlibs/) 
    and pip3 install it (in this order) from the local files.

        - [numpy-1.16.2+mlk](https://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy)
        - [Fiona-1.8.4](https://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona)
        - [Shapely-1.6.4.post1](https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely)
        - [rasterio-1.0.21](https://www.lfd.uci.edu/~gohlke/pythonlibs/#rasterio)
        - [pyproj-2.0.1](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyproj)
        - [OWSLib-0.17.1](https://www.lfd.uci.edu/~gohlke/pythonlibs/#owslib)
        - [Rtree-0.8.3](https://www.lfd.uci.edu/~gohlke/pythonlibs/#rtree)

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
    - Install `spatialindex` library
        ```
        brew install spatialindex
        ```    
    
[Jupyter notebook](https://jupyter.org/) - We recommend using Jupyter notebook for running the **pyIncore** projects. 
It as an open-source application that allows you to create projects (documents) that contain live Python code, 
visualizations and documentation. [Installing Jupyter](https://jupyter.org/install.html) can be done again with pip by 
running `pip3 install jupyter`.

**Optional**: We recommend to use [virtual](https://www.pythonforbeginners.com/basics/how-to-use-python-virtualenv/) environment 
or environment [manager](https://www.anaconda.com/distribution/); tools that help keep dependencies separate for different projects. 
Note that **pyIncore** installation in virtual environments slightly differs from this document. 

## Installation

### All Platforms
 
These steps will guide you on how to install both pyIncore and Jupyter notebook so you can develop your code.

1. Download **pyincore** as an archive file from [NCSA's server](https://incore2.ncsa.illinois.edu/) to a directory on your computer.
2. From the Terminal (Mac/Linux) or Command Prompt (Windows) run:
    ```
    pip3 install --user pyincore_0.2.0.tar.gz
    ```
    
    The installation installs pyIncore and creates a `.incore` folder in your HOME directory to store cached files. 
    A message *pyIncore credentials file has been created at <HOME directory>/.incore/.incorepw* appears 
    in the terminal/prompt. The typical location of a HOME directory is `C:\Users\<username>` on Windows OS, `/Users/<username>` on MacOS 
    and `/home/<username>` on Linux based machines.

**Linux specific notes**

If you see following error, make sure that you installed libspatialindex-dev (see GDAL section above):
```
OSError: Could not find libspatialindex_c library file
```

**Mac specific notes**
    
- We use `matplotlib` library to create graphs. There is a Mac specific installation issue addressed at 
StackOverflow [link1](https://stackoverflow.com/questions/4130355/python-matplotlib-framework-under-macosx) and 
[link2](https://stackoverflow.com/questions/21784641/installation-issue-with-matplotlib-python). In a nutshell, 
insert line:
    ```
    backend : Agg
    ```

    into `~/.matplotlib/matplotlibrc` file.

## Running

- We assume that users develop python script by using pyIncore in their own **Project folder**.
- Locate a file called `.incorepw` in your HOME directory and write your credentials in it; the first line contains your username and the second password. 
The information is used for communicating with **IN-CORE** services such as hazard, data and fragility. 
The file is located in the `.incore` folder created during installation in your HOME directory. The typical path is `C:\Users\<username>` on Windows OS, 
`/Users/<username>` on MacOS and `/home/<username>` on Linux based machines.

- Download the **Building damage analysis** Jupyter notebook (<https://incore2.ncsa.illinois.edu/doc/examples/buildingdamage.ipynb>) 
and verify the installation by running it from your project folder. For details of running and manipulating `ipynb` files refer 
to [Jupyter documentation](https://jupyter.readthedocs.io/en/latest/running.html#running). If you have problems running notebooks, 
contact us at **incore-dev@lists.illinois.edu**.

- Start local **Jupyter notebook** by running the following command at the terminal or command prompt from a **Project folder**:
    ```
    jupyter notebook
    ```
       
    A message *The Jupyter Notebook is running* appears in the terminal/prompt 
    and you should see the notebook open in your browser. 
    Note that you will be asked to copy/paste a token into your browser when you connect 
    for the first time.

- Additionally, a user can run Jupyter notebook interactively in NCSA's [IN-CORE Lab](https://incore-jupyter.ncsa.illinois.edu/hub/login). (*coming soon*)


## Documentation

**pyIncore** documentation can be found on [IN-CORE server](http://incore2.ncsa.illinois.edu/).


## Acknowledgement
This work was performed under financial assistance award 70NANB15H044 from 
the National Institute of Standards and Technology (NIST) as part of 
the Interdependent Networked Community Resilience Modeling 
Environment [(IN-CORE)](http://resilience.colostate.edu/in_core.shtml).