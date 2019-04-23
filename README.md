# pyincore

**pyIncore** is a Python project to analyze and visualize various hazard (earthquake, tornado, hurricane etc.) 
scenarios developed by the Center for Risk-Based Community Resilience Planning team from NCSA. 
The development is part of NIST sponsored IN-CORE (Interdependent Networked Community Resilience Modeling 
Environment) initiative. pyIncore allows users to apply hazards on infrastructure in selected areas. 
Python framework accesses underlying data through local or remote services and facilitates moving and synthesizing 
results.
                      
**pyincore** as a Python module can be used to develop scientific analysis/algorithm.

### Prerequisites

Please read through the instructions at least once completely before actually following them to avoid any installation problems!

**IN-CORE account**

- A user must have an account recognized by the **IN-CORE** service. Please [register](https://identity.ncsa.illinois.edu/register/UUMK36FU2M) 
since your credentials will be required in later steps.

[Python 3.5+](https://www.python.org)

[GDAL](https://www.gdal.org) - Geospatial Data Abstraction Library

- **Linux** 
    **pyIncore** uses `GDAL` library, which has to be installed separately.
    
    - Install **gdal-bin**. Additional information can be found  at the wiki page [How to install GDAL](https://github.com/domlysz/BlenderGIS/wiki/How-to-install-GDAL).
        ```
        sudo apt-get install gdal-bin
        ```
    - Install **libspatialindex-dev**
        ```
        apt-get install libspatialindex-dev
        ```

- **Windows 64bit**
    We provide installation instructions for [Anaconda](https://www.anaconda.com/distribution/) environment manager using [Miniconda](https://docs.conda.io/en/latest/miniconda.html). Python 3.x and GDAL library will be installed with Anaconda/Miniconda. The following instruction is tested for Win 64bit, the 32bit has not been tested yet.
    - Download the latest Miniconda3 installer for Windows from [Miniconda](https://docs.conda.io/en/latest/miniconda.html) web page.
    - Run the installer setup locally (Just Me choice) to avoid the need for administrator privileges.
    - Leave the default folder installation path (`C:\Users\<user>\..\miniconda3`). Do not add Anaconda to the PATH, do add however register Anaconda as the default Python environment.
    Open up an Anaconda prompt from the Windows Start menu, create Python environment (called for example `pyincore`) and activate it
        ```
        conda create -n pyincore python=3
        conda activate pyincore
        ```
 
- **MacOS**
    **pyIncore** uses `GDAL` library, which has to be installed separately. The easiest way is to use [Homebrew](https://brew.sh/), a MacOS package manager.
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