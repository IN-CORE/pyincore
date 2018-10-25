from distutils.core import setup

setup(name = 'pyincore',
      version = '0.2.0',
      packages = ['pyincore', 'pyincore.analyses', 'pyincore.analyses.buildingdamage',
                  'pyincore.analyses.transportationrecovery', 'pyincore.analyses.pipelinedamage',
                  'pyincore.analyses.waternetworkdamage', 'pyincore.analyses.waternetworkrecovery',
                  'pyincore.analyses.waterfacilitydamage', 'pyincore.analyses.bridgedamage',
                  'pyincore.analyses.stochastic_population', 'pyincore.analyses.populationdislocation',
                  'pyincore.analyses.tornadoepndamage', 'pyincore.analyses.nonstructbuildingdamage'],
      requires = ['fiona', 'rasterio', 'jsonpickle', 'numpy', 'shapely', 'scipy', 'matplotlib', 'wikidata', 'requests',
                  'networkx', 'pandas', 'pyproj', 'folium', 'owslib', 'py_expression_eval', 'rtree', 'wntr', 'plotly'])
