from distutils.core import setup

setup(name = 'pyincore',
      version = '0.1.0',
      packages = ['pyincore'],
      requires = ['fiona', 'rasterio', 'jsonpickle', 'numpy', 'shapely', 'scipy', 'matplotlib', 'wikidata', 'requests'])
