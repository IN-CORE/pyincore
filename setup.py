# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from setuptools import setup, find_packages

# version number of pyincore
version = '1.4.1'

with open("README.rst", encoding="utf-8") as f:
    readme = f.read()

setup(
    name='pyincore',
    version=version,
    description='IN-CORE analysis tool python package',
    long_description=readme,
    long_description_content_type='text/x-rst',

    url='https://incore.ncsa.illinois.edu',

    license="Mozilla Public License v2.0",

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

    python_requires=">=3.6",

    install_requires=[
        'fiona==1.8.21',
        'geopandas==0.11.0',
        'matplotlib==3.5.2',
        'networkx==2.8.4',
        'numpy==1.23.0',
        'pandas==1.4.3',
        'pyomo==6.4.1',
        'pyproj==3.2.1',
        'rasterio==1.2.10',
        'requests==2.28.0',
        'rtree==1.0.0',
        'scipy==1.8.1',
        'shapely==1.8.2',
        'wntr==0.4.2',
    ],

    extras_require={
        'test': [
            'pycodestyle==2.8.0',
            'pytest==7.1.2',
            'python-jose==3.3.0',
        ],
        'notebook': [
            'folium==0.12.1.post1',
        ]
    },

    project_urls={
        'Bug Reports': 'https://github.com/IN-CORE/pyincore/issues',
        'Source': 'https://github.com/IN-CORE/pyincore',
    },
)
