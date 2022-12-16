# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import BaseAnalysis
from pyincore import globals as pyglobals
from pyincore.analyses.joplincge.equationlib import *


class SaltLakeCGEModel(BaseAnalysis):
    """A computable general equilibrium (CGE) model is based on fundamental economic principles.
    A CGE model uses multiple data sources to reflect the interactions of households,
    firms and relevant government entities as they contribute to economic activity.
    The model is based on (1) utility-maximizing households that supply labor and capital,
    using the proceeds to pay for goods and services (both locally produced and imported)
    and taxes; (2) the production sector, with perfectly competitive, profit-maximizing firms
    using intermediate inputs, capital, land and labor to produce goods and services for both
    domestic consumption and export; (3) the government sector that collects taxes and uses
    tax revenues in order to finance the provision of public services; and (4) the rest of the world.



    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(SaltLakeCGEModel, self).__init__(incore_client)



    def get_spec(self):
        return {
            'name': 'Salt-Lake-cge',
            'description': 'CGE model for Salt Lake City.',
            'input_parameters': [
                {
                    'id': 'model_iterations',
                    'required': True,
                    'description': 'Number of dynamic model iterations.',
                    'type': int
                },
                {
                    'id': 'solver_path',
                    'required': False,
                    'description': 'Path to ipopt package. If none is provided, it will default to your environment\'ts'
                                   'path to the package.',
                    'type': str
                }

            ],
            'input_datasets': [
                {
                    'id': 'SAM',
                    'required': True,
                    'description': 'Social accounting matrix (SAM) contains data for firms, '
                                   'households and government which are organized in a way to '
                                   'represent the interactions of all three entities in a typical economy.',
                    'type': ['incore:JoplinCGEsam']
                },
                {
                    'id': 'BB',
                    'required': True,
                    'description': 'BB is a matrix which describes how investment in physical infrastructure is'
                                   ' transformed into functioning capital such as commercial and residential buildings.'
                                   ' These data are collected from the Bureau of Economic Analysis (BEA).',
                    'type': ['incore:JoplinCGEbb']
                },
                {
                    'id': 'IOUT',
                    'required': True,
                    'description': 'IOUT is a matrix that describes the transfer of tax revenue collected by the local'
                                   ' government to help finance local government expenditures.',
                    'type': ['incore:JoplinCGEiout']
                },
                {
                    'id': 'MISC',
                    'required': True,
                    'description': 'MISC is the name of a file that contains data for commercial sector employment'
                                   ' and physical capital. It also contains data for the number of households and'
                                   ' working households in the economy.',
                    'type': ['incore:JoplinCGEmisc']
                },
                {
                    'id': 'MISCH',
                    'required': True,
                    'description': 'MISCH is a file that contains elasticities for the supply of labor with'
                                   ' respect to paying income taxes.',
                    'type': ['incore:JoplinCGEmisch']
                },
                {
                    'id': 'LANDCAP',
                    'required': True,
                    'description': 'LANDCAP contains information regarding elasticity values for the response of '
                                   'changes in the price of physical capital with respect to the supply of investment.',
                    'type': ['incore:JoplinCGElandcap']
                },
                {
                    'id': 'EMPLOY',
                    'required': True,
                    'description': 'EMPLOY is a table name containing data for commercial sector employment.',
                    'type': ['incore:JoplinCGEemploy']
                },
                {
                    'id': 'IGTD',
                    'required': True,
                    'description': 'IGTD variable represents a matrix describing the transfer of taxes collected'
                                   ' to a variable which permits governments to spend the tax revenue on workers and'
                                   ' intermediate inputs.',
                    'type': ['incore:JoplinCGEigtd']
                },
                {
                    'id': 'TAUFF',
                    'required': True,
                    'description': 'TAUFF represents social security tax rates',
                    'type': ['incore:JoplinCGEtauff']
                },
                {
                    'id': 'JOBCR',
                    'required': True,
                    'description': 'JOBCR is a matrix describing the supply of workers'
                                   ' coming from each household group in the economy.',
                    'type': ['incore:JoplinCGEjobcr']
                },
                {
                    'id': 'OUTCR',
                    'required': True,
                    'description': 'OUTCR is a matrix describing the number of workers who'
                                   ' live in Joplin but commute outside of town to work.',
                    'type': ['incore:JoplinCGEoutcr']
                },
                {
                    'id': 'sector_shocks',
                    'required': True,
                    'description': 'Aggregation of building functionality states to capital shocks per sector',
                    'type': ['incore:capitalShocks']
                }
            ],
            'output_datasets': [
                {
                    'id': 'domestic-supply',
                    'parent_type': '',
                    'description': 'CSV file of resulting domestic supply',
                    'type': 'incore:Employment'
                },
                {
                    'id': 'gross-income',
                    'parent_type': '',
                    'description': 'CSV file of resulting gross income',
                    'type': 'incore:Employment'
                },
                {
                    'id': 'pre-disaster-factor-demand',
                    'parent_type': '',
                    'description': 'CSV file of factor demand before disaster',
                    'type': 'incore:FactorDemand'
                },
                {
                    'id': 'post-disaster-factor-demand',
                    'parent_type': '',
                    'description': 'CSV file of resulting factor-demand',
                    'type': 'incore:FactorDemand'
                },
                {
                    'id': 'household-count',
                    'parent_type': '',
                    'description': 'CSV file of household count',
                    'type': 'incore:HouseholdCount'
                }
            ]
        }