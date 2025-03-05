# NIST CGE

## Python Models

### Shelby

There are two main scripts for Shelby:

- **'shelby\_CD\_September\_21\_2020.py'**: This is the Shelby CGE model with Cobb-Douglas production function.

- **'shelby\_CES\_September\_21\_2020.py'**: This is the Shelby CGE model with CES (Constant elasticity of substitution) production function.

Both models are created and executed with `runsolver` at the bottom of the script.
Output form 'simulation\_outputs.csv' will be created on the same directory after running script.

## Installation

Anaconda or Miniconda are the preferred python3 package managers for this model. Download from [anaconda.com](https://www.anaconda.com/distribution/). Packages and documentation can be found at [conda-forge.org](https://conda-forge.org/) with installation instructions here: [docs.anaconda.com](https://docs.anaconda.com/anaconda/navigator/install/)

After downloading one of the conda apps, the *environment.yaml* file can be used to build a python3 virtual environment with the correct dependencies.

If conda is not an option, the bare-bones set of dependencies needed are:

- ipopt
- numpy
- pandas
- pyomo

ipopt is part of the COIN project and can be downloaded directly from [coin-or.org](https://projects.coin-or.org/Ipopt) or installed as a package from Anaconda Cloud.
