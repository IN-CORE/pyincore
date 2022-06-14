# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from setuptools import setup, find_packages
import pkg_resources
from pyincore import globals as pyglobals
import pypandoc

pkg_resources.extern.packaging.version.Version = pkg_resources.SetuptoolsLegacyVersion

# use the version from the rasterio module.
version = pyglobals.PACKAGE_VERSION
# use this line for manual versioning like rc version
#version = '1.4.1.rc.4'

with open("README.rst", encoding="utf-8") as f:
    readme = f.read()

setup_args = dict(
    name='pyincore',
    version=version,
    packages=find_packages(where=".", exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    package_data={
        '': ['*.ini']
    },
    description='IN-CORE analysis tool python package',
    long_description=readme,
    # TODO need to figure out what are the dependency requirements
    # TODO this is a hack, really should only be packages needed to run
    install_requires=[line.strip() for line in open("requirements.txt").readlines()],
    python_requires=">=3.6, <3.9",
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
    license="Mozilla Public License v2.0",
    url="https://opensource.ncsa.illinois.edu/bitbucket/projects/INCORE1/repos/pyincore/"
)

setup(**setup_args)