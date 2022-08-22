# Copyright (c) 2022 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import BaseAnalysis, NetworkDataset
from pyincore.utils.networkutil import NetworkUtil
from numpy.linalg import inv
import networkx as nx
import numpy as np
import copy


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
        # Load all dataset-related entities for EPF
        epf_network_dataset = NetworkDataset.from_dataset(self.get_input_dataset('epf_network'))
        epf_network_nodes = epf_network_dataset.nodes.get_dataframe_from_shapefile()
        epf_network_links = epf_network_dataset.links.get_dataframe_from_shapefile()
        epf_graph = epf_network_dataset.get_graph_networkx()

        # Load all dataset-related entities for WDS
        wds_network_dataset = NetworkDataset.from_dataset(self.get_input_dataset('wds_network'))
        wds_network_nodes = wds_network_dataset.nodes.get_dataframe_from_shapefile()
        wds_network_links = wds_network_dataset.links.get_dataframe_from_shapefile()
        wds_graph = wds_network_dataset.get_graph_networkx()

        # Load network interdependencies
        interdependency_table = self.get_input_dataset('interdependency_table').get_dataframe_from_csv()

        # Load restoration functionality and time results for EPF
        epf_func_results = self.get_input_dataset('epf_func_results').get_dataframe_from_csv()
        epf_time_results = self.get_input_dataset('epf_time_results').get_dataframe_from_csv()

        # Load restoration functionality and time results for WDS
        wds_func_results = self.get_input_dataset('wds_func_results').get_dataframe_from_csv()
        wds_time_results = self.get_input_dataset('wds_time_results').get_dataframe_from_csv()

        (epf_cascading_functionality, wds_cascading_functionality) =  self.nci_functionality(epf_network_nodes,
                                                                                             epf_network_links,
                                                                                             epf_graph,
                                                                                             wds_network_nodes,
                                                                                             wds_network_links,
                                                                                             wds_graph,
                                                                                             interdependency_table,
                                                                                             epf_func_results,
                                                                                             epf_time_results,
                                                                                             wds_func_results,
                                                                                             wds_time_results)

        self.set_result_csv_data("epf_cascading_functionality",
                                 epf_cascading_functionality, name=self.get_parameter("epf_cascading_functionality"),
                                 source="dataframe")
        self.set_result_csv_data("wds_cascading_functionality",
                                 wds_cascading_functionality,
                                 name=self.get_parameter("wds_cascading_functionality"),
                                 source="dataframe")

        return True

    def nci_functionality(self, epf_network_nodes, epf_network_links, epf_graph,
                         wds_network_nodes, wds_network_links, wds_graph,
                         interdepedency_table, epf_func_results, epf_time_results,
                         wds_func_results, wds_time_results):
        """Compute EPF and WDS cascading functionality outcomes

        Args:
            epf_network_nodes (pd.DataFrame):
            epf_network_links (pd.DataFrame):
            epf_graph (networkx object):
            wds_network_nodes (pd.DataFrame):
            wds_network_links (pd.DataFrame):
            wds_graph (networkx object):
            interdepedency_table (pd.DataFrame):
            epf_func_results (pd.DataFrame):
            epf_time_results (pd.DataFrame):
            wds_func_results (pd.DataFrame):
            wds_time_results (pd.DataFrame):

        Returns:
            (pd.DataFrame, pd.DataFrame): results for EPF and WDS networks
        """
        return None, None

    def integrate_epf_wds(self):
        pass

    def assemble_epf_discretized_func(self):
        pass

    def assemble_wds_discretized_func(selfs):
        pass

    def solve_leontief_equation(self, epf_wds_graph, epf_wds_functionality_nodes, discretized_days):
        """Computes the solution to the Leontief equation for network interdependency given a

        Args:
            epf_wds_graph (networkx object): graph containing the integrated EPN-WDS network
            epf_wds_functionality_nodes (pd.DataFrame): dataframe containing discretized EFP/WDS restoration results
            per node
            discretized_days (list): days used for discretization of restoration analyses

        Returns:

        """
        # Create a deep copy of the incoming fuctionality results to store new values
        df_functionality_nodes = copy.deepcopy(epf_wds_functionality_nodes)

        for idx in discretized_days:
            M = nx.adjacency_matrix(epf_wds_graph).todense()
            u = 1 - df_functionality_nodes[f'functionality{idx}']
            u = u.to_numpy()
            I = np.identity(len(u))
            q = list(np.dot(np.linalg.inv(I - M.T), u))[0]
            df_functionality_nodes['func_cascading{idx}'] = [0 if i >= 1 else 1 - i for i in q]

        return df_functionality_nodes

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
                    'id': 'epf_network',
                    'required': True,
                    'description': 'EPN network to merge via dependencies',
                    'type': ['incore:epnNetwork'],
                },
                {
                    'id': 'wds_network',
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

                    'id': 'epf_func_results',
                    'required': True,
                    'description': 'A csv file recording discretized EPF functionality over time',
                    'type': ['incore:epfDiscretizedRestorationFunc']
                },
                {

                    'id': 'epf_time_results',
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