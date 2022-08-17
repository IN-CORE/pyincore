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

    def nci_functionality(self):
        pass

    def get_spec(self):
        """Get specifications of the network cascading interdependency functionality analysis.
        Returns:
            obj: A JSON object of specifications of the NCI functionality analysis.
        """
        return {
            'name': 'wfn-functionality',
            'description': 'water facility network functionality analysis',
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
                    'id': 'network_a',
                    'required': True,
                    'description': 'Network A to merge via dependencies',
                    'type': ['incore:epnNetwork', 'incore:waterNetwork'],
                },
                {
                    'id': 'network_b',
                    'required': True,
                    'description': 'Network B to merge via dependencies',
                    'type': ['incore:epnNetwork', 'incore:waterNetwork'],
                },
                {
                    'id': 'interdepency_ab_table',
                    'required': True,
                    'description': 'Table containing interdependency information between networks A and B',
                    'type': 'incore:networkInterdependencyTable'
                },
                {

                    'id': 'func_results_a',
                    'parent_type': '',
                    'description': 'A csv file recording discretized functionality over time',
                    'type': ['incore:epfDiscretizedRestorationFunc', 'incore:waterFacilityDiscretizedRestorationFunc']
                },
                {

                    'id': 'func_results_b',
                    'parent_type': '',
                    'description': 'A csv file recording discretized functionality over time',
                    'type': ['incore:epfDiscretizedRestorationFunc', 'incore:waterFacilityDiscretizedRestorationFunc']
                }
            ],
            'output_datasets': [
                {
                    'id': 'failure_probability',
                    'description': 'CSV file of failure probability',
                    'type': 'incore:failureProbability'
                },
                {
                    'id': 'sample_failure_state',
                    'description': 'CSV file of failure state for each sample',
                    'type': 'incore:sampleFailureState'
                },
            ]
        }