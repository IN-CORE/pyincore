# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from setuptools import setup, find_packages

setup(name = 'pyincore',
      version = '0.2.0',
      packages =  find_packages(where=".", exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      install_requires = ['fiona', 'rasterio', 'jsonpickle', 'numpy', 'shapely', 'scipy', 'matplotlib', 'wikidata', 'requests',
                  'networkx', 'pandas', 'pyproj', 'folium', 'owslib', 'py_expression_eval', 'rtree', 'wntr', 'plotly', 'pyyaml'])
