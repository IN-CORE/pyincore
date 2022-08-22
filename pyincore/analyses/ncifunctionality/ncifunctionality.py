# Copyright (c) 2022 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import BaseAnalysis
from pyincore.utils.networkutil import NetworkUtil


class NciFunctionality(BaseAnalysis):
    """
    This analysis computes the output of the Leontief equation for functional dependencies between two
    interdependent networks having functionality information per node. These dependencies capture cascading
    dependencies on infrastructure functionality, expressed in terms of discrete points.

    The output of the computation consists of two datasets, one per each labeled network, with new cascading
    functionalities accompanying the original discrete ones.

    Contributors
        | Science: Milad Roohi, John van de Lindt
        | Implementation: Milad Roohi, Santiago Núñez-Corrales and NCSA IN-CORE Dev Team

    Related publications

        Roohi M, van de Lindt JW, Rosenheim N, Hu Y, Cutler H. (2021) Implication of building inventory accuracy
        on physical and socio-economic resilience metrics for informed decision-making in natural hazards.
        Structure and Infrastructure Engineering. 2020 Nov 20;17(4):534-54.

        Milad Roohi, Jiate Li, John van de Lindt. (2022) Seismic Functionality Analysis of Interdependent
        Buildings and Lifeline Systems 12th National Conference on Earthquake Engineering (12NCEE),
        Salt Lake City, UT (June 27-July 1, 2022).


    Args:

        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(NciFunctionality, self).__init__(incore_client)

    def run(self):
        pass

    def network_cascading_interdependency_functionality(self):
        pass

    def integrate_epf_wds(self):
        pass

    def assemble_epf_discretized_func(self):
        pass

    def assemble_wds_discretized_func(selfs):
        pass

    def solve_leontief_equation(self):
        pass

    def get_discretized_days_cols(self, epf_restoration_results):
        pass

    def get_spec(self):
        """Get specifications of the network cascading interdependency functionality analysis.
        Returns:
            obj: A JSON object of specifications of the NCI functionality analysis.
        """
        return {
            'name': 'network-cascading-interdepedency-functionality',
            'description': 'Network cascading interdepedency functionality analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                }
            ],
            'input_datasets': [
                {
                    'id': 'network_epn',
                    'required': True,
                    'description': 'EPN network to merge via dependencies',
                    'type': ['incore:epnNetwork'],
                },
                {
                    'id': 'network_wds',
                    'required': True,
                    'description': 'WDS network to merge via dependencies',
                    'type': ['incore:epnNetwork', 'incore:waterNetwork'],
                },
                {
                    'id': 'interdependency_table',
                    'required': True,
                    'description': 'Table containing interdependency information between EPN na WDS networks',
                    'type': 'incore:networkInterdependencyTable'
                },
                {

                    'id': 'epn_func_results',
                    'required': True,
                    'description': 'A csv file recording discretized EPN functionality over time',
                    'type': ['incore:epfDiscretizedRestorationFunc']
                },
                {

                    'id': 'epn_time_results',
                    'required': True,
                    'description': 'A csv file recording repair time for EPF per class and limit state',
                    'type': ['incore:epfRestorationTime']
                },
                {

                    'id': 'wds_func_results',
                    'required': True,
                    'description': 'A csv file recording discretized WDS functionality over time',
                    'type': ['incore:waterFacilityDiscretizedRestorationFunc']
                },
                {

                    'id': 'wds_time_results',
                    'required': True,
                    'description': 'A csv file recording repair time for WDS per class and limit state',
                    'type': ['incore:waterFacilityRestorationTime']
                }
            ],
            'output_datasets': [
                {
                    'id': 'epf_cascading_functionality',
                    'description': 'CSV file of interdependent cascading network functionality for EPF',
                    'type': 'incore:epfDiscretizedCascadingFunc'
                },
                {
                    'id': 'wds_cascading_functionality',
                    'description': 'CSV file of interdependent cascading network functionality for WDS',
                    'type': 'incore:waterFacilityDiscretizedCascadingFunc'
                }
            ]
        }