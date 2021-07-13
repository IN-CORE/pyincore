# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from setuptools import setup, find_packages

setup(
    name='pyincore',
    version='0.9.4',
    packages=find_packages(where=".", exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    package_data={
        '': ['*.ini']
    },
    description='IN-CORE analysis tool python package',
    long_description=("pyIncore is a Python package to analyze and visualize various hazard "
                      "(earthquake, tornado, hurricane etc.) scenarios developed "
                      "by the Center for Risk-Based Community Resilience Planning team from NCSA. "
                      "The development is part of NIST sponsored IN-CORE (Interdependent Networked Community "
                      "Resilience Modeling Environment) initiative. "
                      "pyIncore allows users to apply hazards on infrastructure in selected areas. "
                      "Python framework accesses underlying data through local or remote services "
                      "and facilitates moving and synthesizing results."),
    # TODO need to figure out what are the dependency requirements
    # TODO this is a hack, really should only be packages needed to run
    install_requires=[line.strip() for line in open("requirements.txt").readlines()],
    python_requires=">=3.6",
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
