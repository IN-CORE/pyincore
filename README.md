# pyincore

**Pyincore** is a Python package to analyze and visualize various hazard (earthquake, tornado, hurricane etc.) 
scenarios developed by the Center for Risk-Based Community Resilence Planning team from NCSA. 
The development is part of NIST sponsored IN-CORE (Interdependent Networked Community Resilience Modeling 
Environment) initiative. Pyincore allows users to apply hazards on infrastructure in selected areas. 
Python framework acceses underlying data through local or remote services and facilitates moving 
and synthesizing results.
                      
**Pyincore** as a python module can be used to write hazard workflow tools.

# Installation

You will need to have Python 3 installed for this method. To install the package, 
download the source code from [Git](https://git.ncsa.illinois.edu/incore/pyincore) 
repository

and then use one of the following methods to install the package.

Mac
---

1. Clone the code from [Git](https://git.ncsa.illinois.edu/incore/pyincore) 
repository.
2. We recommend using virtual environments, `virtualenv` for python 3.5+. for managing Python environments.  
    
    `virtualenv --python=python3.6 farmdoc`
    `source venv/bin/activate`

3. From the terminal at the project folder run:

    `python setup.py install`
    
4. Install required packages individually if necessary. For example, `spatialindex` library 
 could cause problems, use [Homebrew](https://brew.sh/) or `pip` for installing it:
  
    `brew install spatialindex`
    
    `pip install matplotlib==2.1.0`

# Running

Run from pyincore folder: 

    `git branch -a`
    
4. Run a script with parameters (use `-h` for help) 


### For developers
```
git clone https://git.ncsa.illinois.edu/incore/pyincore/forge.git
cd pyincore
pip install -e .
```

# Documentation

Pyincore documentation can be found on [Incore server](http://incore2.ncsa.illinois.edu).
Tutorials and examples can be found in the `docs` directory. The Jupyter notebooks can be run 
interactively with  [Jupyter](http://jupyter.org/install).

### For developers
Pyincore documentation uses Sphinx as a bulding tool. In order to run Sphinx, you need to install 
`sphinx` and `sphinx_rtd_theme` modules by using, for example `pip`:

```
pip install -U sphinx
pip install -U sphinx_rtd_theme
```

From the **docs** folder run following commant to build the documentation:

```
sphinx-build -b html source build
```


# Pyincore tests
In order to run Tests, you need to create a file called, ".incorepw" under tests folder.
The file needs two lines: user name in 1st line, password in 2nd line


# Notes

There is a known issue running analyses on multiple threads in some versions of python 3.6.x running on MacOS High Sierra 10.13.x
If you see such errors on your environment, set the below environment variable in your .bash_profile as a workaround.

`export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES`  
 
Issue details can be found [here](http://sealiesoftware.com/blog/archive/2017/6/5/Objective-C_and_fork_in_macOS_1013.html)


# Requirements
* Pyincore requires Python 3.5 or greater.
* To access data in the Incore, you must have an account recognized by Incore Auth, 
or a [free Incore ID](https://incore.ncsa.illinois.edu).

# Contributions
If you find a bug or want a feature, feel free to open an issue on NCSA GitLab.


# Support
This work was performed under financial assistance award 70NANB15H044 from 
the National Institute of Standards and Technology (NIST) as part of 
the Interdependent Networked Community Resilience Modeling 
Environment [(IN-CORE)](http://resilience.colostate.edu/in_core.shtml).