# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from setuptools import setup, find_packages
from pyincore import globals as pyglobals

# use the version from the rasterio module.
version = pyglobals.PACKAGE_VERSION
# use this line for manual versioning like rc version
#version = '1.4.1.rc.4'

with open("README.rst", encoding="utf-8") as f:
    readme = f.read()

setup(
    name='pyincore',
    version=version,
    description='IN-CORE analysis tool python package',
    long_description=readme,

    url='https://incore.ncsa.illinois.edu',

    license="Mozilla Public License v2.0",

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        "Topic :: Scientific/Engineering"
    ],

    keywords=[
        "infrastructure",
        "resilience",
        "hazards",
        "data discovery",
        "IN-CORE",
        "earthquake",
        "tsunami",
        "tornado",
        "hurricane",
        "dislocation"
    ],

    packages=find_packages(where=".", exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    package_data={
        '': ['*.ini']
    },

    python_requires=">=3.6, <3.9",

    install_requires=[
        'fiona',
        'geopandas',
        'jsonpickle',
        'matplotlib',
        'networkx',
        'pandas',
        'pyomo',
        'pyproj',
        'rasterio',
        'requests',
        'scipy',
        'wntr',
    ],

    extras_require={
        'test': [
            'folium',
            'python-jose',
            'rtree'
        ],
    },

    project_urls={ 
        'Bug Reports': 'https://github.com/IN-CORE/pyincore/issues',
        'Source': 'https://github.com/IN-CORE/pyincore',
    },
)
