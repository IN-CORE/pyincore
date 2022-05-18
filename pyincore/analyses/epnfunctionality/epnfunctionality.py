# Copyright (c) 2022 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import BaseAnalysis
from pyincore.analyses.montecarlofailureprobability import MonteCarloFailureProbability

import numpy as np
import pandas as pd
import networkx as nx


class EpnFunctionality(BaseAnalysis):
    """
    This analysis computes expected electric network functionality using results from
    Monte Carlo damage.

    The computation proceeds by using Monte Carlo data for electric facilities to obtain,
    and for each realization, obtains all shortest paths and preserves those with finite length.

    The output of the computation is a network containing functionality information for electric power
    network infrastructure elements.

    Contributors
        | Science: Paolo Gardoni, Neetesh Sharma, Armin Tabandeh
        | Implementation: Paolo Gardoni, Neetesh Sharma, Armin Tabandeh, Santiago Núñez-Corrales, and NCSA IN-CORE Dev Team

    Related publications
        Sharma, N., & Gardoni, P. (2019). Modeling the time-varying performance of electrical infrastructure during
        post-disaster recovery using tensors. In P. Gardoni (Ed.), Handbook of sustainable and resilient infrastructure
        (pp. 259–276). New York, NY: Routledge.

    Args:
        incore_client (IncoreClient): Service authentication.
    """

    def __init__(self, incore_client):
        super(EpnFunctionality, self).__init__(incore_client)

    def run(self):
        """Execute the EPN functionality analysis using parameters and input data."""
        pass

    def get_spec(self):
        """Get specifications of the housing serial recovery model.

                Returns:
                    obj: A JSON object of specifications of the housing serial recovery model.

                """
        return {
            'name': 'epn-functionality',
            'description': 'Electric power network functionality',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'Result CSV dataset name',
                    'type': str
                },
                {
                    'id': 'gate_station_nodes',
                    'required': True,
                    'description': 'Gate station nodes',
                    'type': [int]
                },
                {
                    'id': 'samples',
                    'required': False,
                    'description': 'Number of samples to consider from the Monte Carlo'
                                   'electric power facility damage analysis, defaults to 1000',
                    'type': int
                },
                {
                    'id': 'effective_infinity',
                    'required': False,
                    'description': 'Value utilized to represent an effectively infinite distance,'
                                   'defaults to 9999',
                    'type': int
                }
            ],
            'input_datasets': [
                {
                    'id': 'epf_damage',
                    'required': True,
                    'description': 'A csv file with electric power facility damage'
                                   'results',
                    'type': 'incore:epfDamageVer3'
                }
            ],
            'output_datasets': [
                {
                    'id': 'ds_result',
                    'parent_type': 'epn_functionality',
                    'description': 'An electric power network with functionality data',
                    'type': 'incore:epnFunctionality'
                }
            ]
        }