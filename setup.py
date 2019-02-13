# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from setuptools import setup, find_packages

setup(
    name='pyincore',
    version='0.1.0',
    packages=find_packages(where=".", exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    description='Incore analysis tool python package',
    long_description=("Pyincore is a Python package to analyze and visualize various hazard "
                      "(earthquake, tornado, hurricane etc.) scenarios developed "
                      "by the Center for Risk-Based Community Resilence Planning team from NCSA. "
                      "The development is part of NIST sponsored IN-CORE (Interdependent Networked Community "
                      "Resilience Modeling Environment) initiative. "
                      "Pyincore allows users to apply hazards on infrastructure in selected areas. "
                      "Python framework acceses underlying data through local or remote services "
                      "and facilitates moving and synthesizing results."),
    install_requires=[
        "fiona>=1.8.4",
        "folium>=0.7.0",
        "jsonpickle>=1.1",
        "matplotlib>=2.1.0",
        "networkx>=2.2",
        "numpy>=1.16.1",
        "owslib>=0.17.1",
        "pandas>=0.24.1",
        "plotly>=3.6.0",
        "py-expression-eval>=0.3.6",
        "pyproj>=1.9.6",
        "pyyaml>=3.13",
        "rasterio>=1.0.18",
        "requests>=2.21.0",
        "rtree>=0.8.3",
        "scipy>=1.2.0",
        "shapely>=1.6.4.post2",
        "wikidata>=0.6.1",
        "wntr>=0.1.6",
    ],
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 2 - Beta",
        "Intended Audience :: Risk-Based Community/Science/Research/Public",
        "License :: Mozilla Public License v2.0",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Resilience/Hazard/Scientific/Planning"
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
