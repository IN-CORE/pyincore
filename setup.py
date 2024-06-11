# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from setuptools import setup, find_packages

# version number of pyincore
version = '1.19.0'

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
        '': ['*.ini', "*.csv"]
    },

    python_requires=">=3.9",

    install_requires=[
        'fiona>=1.9.5',
        'geopandas>=0.14.0',
        'matplotlib>=3.8.0',
        'networkx>=3.2.1',
        'numpy>=1.26.0,<2.0a0',
        'pandas>=2.1.2',
        'pyomo>=6.6.2',
        'pyproj>=3.6.1',
        'rasterio>=1.3.9',
        'rtree>=1.1.0',
        'scipy>=1.11.3',
        'shapely>=2.0.2',
        'Deprecated>=1.2.14'
    ],

    extras_require={
        'test': [
            'pycodestyle>=2.6.0',
            'pytest>=3.9.0',
            'python-jose>=3.0',
        ]
    },

    project_urls={
        'Bug Reports': 'https://github.com/IN-CORE/pyincore/issues',
        'Source': 'https://github.com/IN-CORE/pyincore',
    },
)
