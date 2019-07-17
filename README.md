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

**Virtual environment**

We provide installation instructions for environment manager using [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/distribution/), tools that help keep dependencies separate for different projects. 
- Download the latest [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/distribution/#download-section) installer.
- Run the installer setup locally to avoid the need for administrator privileges.
- Leave the default folder installation path. Do not add Anaconda to the PATH; however, you should register Anaconda as the default Python environment.
Open up an Anaconda prompt from the Windows Start menu or Terminal, create Python environment (required for the `pyincore` example) and activate it
        ```
        conda create -n pyincore python=3
        conda activate pyincore
        ```
        
[**Python 3.5+**](https://www.python.org)

- Anaconda/Miniconda will include Python (Anaconda also includes a collection of over 1,500+ open source packages), so installing Python first isn't needed. 
- It is common to have more than one Python version installed on your computer. Make sure you are running the correct, Anaconda/Miniconda version of Python.
    
[**Jupyter notebook**](https://jupyter.org/) 

- We recommend using Jupyter notebook for running the **pyIncore** projects. 
It as an open-source application that allows you to create projects (documents) that contain live Python code, 
visualizations and documentation. Jupyter Notebook is already installed with Anaconda distribution; it has to be installed separately in your virtual environment.

## Installation

### All Platforms
 
These steps will guide you on how to install both pyIncore and Jupyter notebook so you can develop your code.

1.	Add [conda-forge](https://conda-forge.org/) package repository, conda-forge channel to your environment:
    ```
    conda config –add channels conda-forge
    ```

2. Add NCSA’s **pyincore** conda channel to your environment:
    ```
    conda config --append channels https://username:password@incore2.ncsa.illinois.edu/conda/pyincore/

    ```

3. From the Terminal (Mac/Linux) or Command Prompt (Windows) run:
    ```
    conda install pyincore
    ```
    
    The installation installs pyIncore and creates a `.incore` folder in your HOME directory to store cached files. 
    A message *pyIncore credentials file has been created at <HOME directory>/.incore/.incorepw* appears 
    in the terminal/prompt. The typical location of a HOME directory is `C:\Users\<username>` on Windows OS, `/Users/<username>` on MacOS 
    and `/home/<username>` on Linux based machines.

**Mac specific notes**
    
- We use `matplotlib` library to create graphs. There is a Mac specific installation issue addressed at [here](https://stackoverflow.com/questions/4130355/python-matplotlib-framework-under-macosx) and 
[here](https://stackoverflow.com/questions/21784641/installation-issue-with-matplotlib-python). In a nutshell, 
insert line: `backend : Agg` into `~/.matplotlib/matplotlibrc` file.

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

- Start local **Jupyter notebook** by running the following command at the terminal or command prompt from a **Project folder**.:
    ```
    jupyter notebook
    ```
       
    A message *The Jupyter Notebook is running* appears in the terminal/prompt 
    and you should see the notebook open in your browser. 
    You will be asked to copy/paste a token into your browser when you connect 
    for the first time. **Note** that the notebook is already installed with Anaconda 
    distribution however it has to be installed separately in your virtual environment 
    on Miniconda by running `conda install jupyter`.

- Additionally, a user can run Jupyter notebook interactively in NCSA's [IN-CORE Lab](https://incore-jupyter.ncsa.illinois.edu/hub/login). (*coming soon*)


## Documentation

**pyIncore** documentation can be found on [IN-CORE server](http://incore2.ncsa.illinois.edu/).


## Acknowledgement
This work was performed under financial assistance award 70NANB15H044 from 
the National Institute of Standards and Technology (NIST) as part of 
the Interdependent Networked Community Resilience Modeling 
Environment [(IN-CORE)](http://resilience.colostate.edu/in_core.shtml).