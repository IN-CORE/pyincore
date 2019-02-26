# pyincore

**Pyincore** is a Python package to analyze and visualize various hazard (earthquake, tornado, hurricane etc.) 
scenarios developed by the Center for Risk-Based Community Resilence Planning team from NCSA. 
The development is part of NIST sponsored IN-CORE (Interdependent Networked Community Resilience Modeling 
Environment) initiative. Pyincore allows users to apply hazards on infrastructure in selected areas. 
Python framework acceses underlying data through local or remote services and facilitates moving 
and synthesizing results.
                      
**Pyincore** as a python module can be used to write hazard workflow tools. We envision users writing tools 
as a [Jupyter](https://jupyter.org/) notebooks.

### Prerequisites

A user must have an account recognized by the **Incore** service. [Contact us](https://incore.ncsa.illinois.edu), please 
and credentials will be sent to you.

[Python 3.5](https://www.python.org) or greater

[GDAL](https://www.gdal.org) - Geospatial Data Abstraction Library

- **Linux** 

    **Pyincore** uses GDAL library which has to be installed separately for example by using `apt-get` package utility 
    on Debian, Ubuntu, and related Linux distributions.
    ```
    apt-get gdal
    ```
    Additonal information can be found  at the wiki page [How to install GDAL](https://github.com/domlysz/BlenderGIS/wiki/How-to-install-GDAL).
- **Windows**

    GDAL for Windows can be difficult to build, requiring a number of prerequisite software, libraries, and header files. 
    If you are comfortable building Windows software then building GDAL from source as a develop build is preferred.
    
    If you are not comfortable building GDAL then you may want to download the `gdal` binaries 
    from [Windows Binaries for Python](https://www.lfd.uci.edu/~gohlke/pythonlibs/). 
    The problem with this is that GDAL header files 
    are not included, so you cannot do a `pip install` of packages that want to utilize 
    the GDAL headers. Fiona and Rasterio will need binaries installed from this page as well, 
    and if you run into failed dependancies during the setup process you may want to revisit 
    the page and install the binaries for the Python extensions that are causing problems. 
    Additional information can be found at the wiki page [How to install GDAL](https://github.com/domlysz/BlenderGIS/wiki/How-to-install-GDAL).


**Optional**: `virtualenv` (available by running `pip install virtualenv`) or [Anaconda](https://www.anaconda.com/distribution/), 
note that a full Anaconda distribution will include Python, so installing Python first isn't needed if you use Anaconda

## Installation

### All Platforms

1. Download **pyincore** as an archive file from NCSA's server.
2. Change into the ```pyincore``` directory (or prepend the path to the directory onto files reference from here on out)
3. **Optional**: Activate your virtual or conda environment
4. From the terminal, in the project folder (pyincore) run:
    ```
    python setup.py install
    ```
5. Verify the installation
    ```
    python setup.py test
    ```

    **Windows specific installation notes**
    
    - Open the `Anaconda` prompt, or `cmd` depending on if you are using Anaconda or not before you activate 
    virtual environment (step 3 above)

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

- Verify the installation by running the test script
    ```
    python setup.py test
    ```
- Run **[Jupyter](https://jupyter.org/) notebook** interactively in ([Incore Lab](https://incore-jupyter.ncsa.illinois.edu/hub/login) lab).

## Documentation

**Pyincore** documentation can be found on [Incore server](http://incore2.ncsa.illinois.edu/).


## Acknowledgement
This work was performed under financial assistance award 70NANB15H044 from 
the National Institute of Standards and Technology (NIST) as part of 
the Interdependent Networked Community Resilience Modeling 
Environment [(IN-CORE)](http://resilience.colostate.edu/in_core.shtml).