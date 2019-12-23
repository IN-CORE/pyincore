# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from setuptools import setup, find_packages

setup(
    name='pyincore',
    version='0.5.4',
    packages=find_packages(where=".", exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    package_data={
        '': ['*.ini']
    },
    description='IN-CORE analysis tool python package',
    long_description=("pyIncore is a Python package to analyze and visualize various hazard "
                      "(earthquake, tornado, hurricane etc.) scenarios developed "
                      "by the Center for Risk-Based Community Resilence Planning team from NCSA. "
                      "The development is part of NIST sponsored IN-CORE (Interdependent Networked Community "
                      "Resilience Modeling Environment) initiative. "
                      "pyIncore allows users to apply hazards on infrastructure in selected areas. "
                      "Python framework acceses underlying data through local or remote services "
                      "and facilitates moving and synthesizing results."),
    install_requires=[
        "fiona>=1.8.4",
        "jsonpickle>=1.1",
        "networkx>=2.2",
        "numpy>=1.16.1",
        "owslib>=0.17.1",
        "pandas>=0.24.1",
        "pyproj>=1.9.6",
        "pyyaml>=3.13",
        "rasterio>=1.0.18",
        "requests>=2.21.0",
        "rtree>=0.8.3",
        "scipy>=1.2.0",
        "shapely>=1.6.4.post1",
        "wntr>=0.1.6",
        "pyomo>=5.6",
        "pytest>=3.9.0",
        "python-jose>=3.0"
    ],
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering"
    ],
    keywords=[
        "infrastructure",
        "resilence",
        "hazards",
        "data discovery",
        "IN-CORE",
        "earthquake",
        "tsunami",
        "tornado",
        "hurricane",
        "dislocation"
    ],
    license="Mozilla Public License v2.0",
    url="https://git.ncsa.illinois.edu/incore/pyincore"
)
