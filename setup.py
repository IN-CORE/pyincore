from distutils.core import setup

setup(name = 'pyincore',
      version = '0.2.0',
      packages = ['pyincore', 'pyincore.analyses', 'pyincore.analyses.buildingdamage', 'pyincore.analyses.waterfacilitydamage',
                  'pyincore.analyses.transportationrecovery', 'pyincore.analyses.pipelinedamage', 'pyincore.analyses.bridgedamage'],
      requires = ['fiona', 'rasterio', 'jsonpickle', 'numpy', 'shapely', 'scipy', 'matplotlib', 'wikidata', 'requests',
                  'networkx', 'pandas', 'folium', 'owslib', 'py_expression_eval'])
