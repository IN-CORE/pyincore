# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import copy

import numpy as np
import pandas as pd
import networkx as nx

from pyincore import BaseAnalysis, NetworkDataset
from pyincore.analyses.epnfunctionality.epnfunctionalityutil import EpnFunctionalityUtil


class EpnFunctionality(BaseAnalysis):
    """Computes electric power infrastructure functionality.
    Args:
        incore_client: Service client with authentication info
    """

    def __init__(self, incore_client):
        super(EpnFunctionality, self).__init__(incore_client)

    def run(self):
        """Execute eletric power facility functionality analysis """

        # get network dataset
        network_dataset = NetworkDataset.from_dataset(self.get_input_dataset("epn_network"))
        edges_epl_gdf = network_dataset.links.get_dataframe_from_shapefile()
        nodes_epf_gdf = network_dataset.nodes.get_dataframe_from_shapefile()
        edges_epl_gdf['weight'] = edges_epl_gdf.loc[:, 'length_km']
        G_ep = network_dataset.get_graph_networkx()

        # get epf sample
        num_samples = self.get_parameter("num_samples")
        # TODO: there must be more elegant way to handle this
        sampcols = ['s' + samp for samp in np.arange(num_samples).astype(str)]
        epf_dmg_fs = self.get_input_dataset('epf_sample_failure_state').get_dataframe_from_csv()

        epf_sample_df = pd.DataFrame(
            np.array([np.array(epf_dmg_fs.failure.values[i].split(',')).astype('int')
                      for i in np.arange(epf_dmg_fs.shape[0])]),
            index=epf_dmg_fs.guid.values, columns=sampcols)
        epf_sample_df1 = nodes_epf_gdf.loc[:, ['guid', 'nodenwid']].set_index('guid').join(epf_sample_df)

        # get gate station nodes
        gatestation_nodes_class = self.get_parameter("gate_station_node_class")
        if gatestation_nodes_class is None:
            # default to EPPL
            gatestation_nodes_class = 'EPPL'

        # get the guid from the matching class
        gate_station_nodes = nodes_epf_gdf[nodes_epf_gdf["utilfcltyc"] == gatestation_nodes_class]["nodenwid"].to_list()

        # calculate the distribution nodes
        distributionsub_nodes = list(set(list(G_ep.nodes)) - set(gate_station_nodes))

        (fs_results, fp_results) = self.epf_functionality(distributionsub_nodes, gate_station_nodes, num_samples,
                                                          sampcols, epf_sample_df1, G_ep)

        self.set_result_csv_data("sample_failure_state",
                                 fs_results, name=self.get_parameter("result_name") + "_failure_state",
                                 source="dataframe")
        self.set_result_csv_data("failure_probability",
                                 fp_results,
                                 name=self.get_parameter("result_name") + "_failure_probability",
                                 source="dataframe")

        return True

    def epf_functionality(self, distributionsub_nodes, gate_station_nodes, num_samples, sampcols, epf_sample_df1, G_ep):
        """Run pipeline functionality analysis for multiple pipelines.
        Args:
        Returns:

        """

        # a distance of M denotes disconnection
        M = 9999
        func_ep_df = pd.DataFrame(np.zeros((len(distributionsub_nodes), num_samples)), index=distributionsub_nodes,
                                  columns=sampcols)

        for si, scol in enumerate(sampcols):
            nodestate_ep = epf_sample_df1.loc[:, ['nodenwid', scol]]
            linkstate_ep = None
            badlinks_ep = EpnFunctionalityUtil.get_bad_edges(G_ep, nodestate_ep, linkstate_ep, scol)
            badlinkdict_ep = {k: {'weight': M} for k in badlinks_ep}
            G1_ep = copy.deepcopy(G_ep)
            nx.set_edge_attributes(G1_ep, badlinkdict_ep)
            res_ep = EpnFunctionalityUtil.network_shortest_paths(G1_ep, gate_station_nodes, distributionsub_nodes)
            func_ep_df.loc[distributionsub_nodes, scol] = (res_ep < M) * 1

        # use nodenwid index to get its guid
        fs_temp = pd.merge(func_ep_df, epf_sample_df1["nodenwid"], left_index=True, right_on="nodenwid",
                           how='left').drop(columns=["nodenwid"])
        fp_temp = fs_temp.copy(deep=True)

        # shape the dataframe into failure probability and failure samples
        fs_temp['failure'] = fs_temp.astype(str).apply(','.join, axis=1)
        fs_results = fs_temp.filter(['failure'])
        fs_results.reset_index(inplace=True)
        fs_results = fs_results.rename(columns={'index': 'guid'})

        # calculate failure probability
        # count of 0s divided by sample size
        fp_temp["failure_probability"] = (num_samples - fp_temp.sum(axis=1).astype(int)) / num_samples
        fp_results = fp_temp.filter(['failure_probability'])
        fp_results.reset_index(inplace=True)
        fp_results = fp_results.rename(columns={'index': 'guid'})

        return fs_results, fp_results

    def get_spec(self):
        """Get specifications of the pipeline functionality analysis.
        Returns:
            obj: A JSON object of specifications of the pipeline functionality analysis.
        """
        return {
            'name': 'pipeline-functionlaity',
            'description': 'buried pipeline functionality analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                },
                {
                    'id': 'num_samples',
                    'required': True,
                    'description': 'Number of MC samples',
                    'type': int
                },
                {
                    'id': 'gate_station_node_class',
                    'required': False,
                    'description': "class of the gate station nodes. Default to EPPL",
                    'type': str
                }
            ],
            'input_datasets': [
                {
                    'id': 'epn_network',
                    'required': True,
                    'description': 'EPN Network Dataset',
                    'type': ['incore:network'],
                },
                {
                    'id': 'epf_sample_failure_state',
                    'required': True,
                    'description': 'CSV file of failure state for each sample. Output from MCS analysis',
                    'type': 'incore:sampleFailureState'
                },
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
