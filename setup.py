"""

Copyright (c) 2019 University of Illinois and others.  All rights reserved.
This program and the accompanying materials are made available under the
terms of the Mozilla Public License v2.0 which accompanies this distribution,
and is available at https://www.mozilla.org/en-US/MPL/2.0/

"""

from distutils.core import setup

setup(name = 'pyincore',
      version = '0.2.0',
      packages = ['pyincore', 'pyincore.analyses', 'pyincore.analyses.buildingdamage',
                  'pyincore.analyses.transportationrecovery', 'pyincore.analyses.pipelinedamage',
                  'pyincore.analyses.waternetworkdamage', 'pyincore.analyses.waternetworkrecovery',
                  'pyincore.analyses.waterfacilitydamage', 'pyincore.analyses.bridgedamage',
                  'pyincore.analyses.stochasticpopulation', 'pyincore.analyses.populationdislocation',
                  'pyincore.analyses.tornadoepndamage', 'pyincore.analyses.nonstructbuildingdamage',
                  'pyincore.analyses.cumulative_building_damage'],
      requires = ['fiona', 'rasterio', 'jsonpickle', 'numpy', 'shapely', 'scipy', 'matplotlib', 'wikidata', 'requests',
                  'networkx', 'pandas', 'pyproj', 'folium', 'owslib', 'py_expression_eval', 'rtree', 'wntr', 'plotly'])
