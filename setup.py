from setuptools import setup, find_packages

setup(name = 'pyincore',
      version = '0.2.0',
      packages =  find_packages(where=".", exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      install_requires = ['fiona', 'rasterio', 'jsonpickle', 'numpy', 'shapely', 'scipy', 'matplotlib', 'wikidata', 'requests',
                  'networkx', 'pandas', 'pyproj', 'folium', 'owslib', 'py_expression_eval', 'rtree', 'wntr', 'plotly', 'pyyaml'])
