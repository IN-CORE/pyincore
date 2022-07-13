# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import copy

import numpy as np
import pandas as pd
import networkx as nx

from pyincore import BaseAnalysis
from pyincore.analyses.epffunctionality import EpfFunctionalityUtil


class EpfFunctionality(BaseAnalysis):
    """Computes electric power infrastructure functionality.
    Args:
        incore_client: Service client with authentication info
    """

    def __init__(self, incore_client):
        super(EpfFunctionality, self).__init__(incore_client)

    def run(self):
        """Execute eletric power facility functionality analysis """
        nodes_epf_gdf = self.get_input_dataset("").powerfacility_dataset.get_dataframe_from_shapefile()
        edges_epl_gdf = self.get_input_dataset("").get_dataframe_from_shapefile()
        edges_epl_gdf['weight'] = edges_epl_gdf.loc[:, 'length_km']
        G_ep = EpfFunctionalityUtil.gdf_to_nx(nodes_epf_gdf,edges_epl_gdf)

        num_samples = self.get_parameter("num_samples")
        gatestation_nodes = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        distributionsub_nodes = list(set(list(G_ep.nodes)) - set(gatestation_nodes))
        epf_sample_df1 =


        (fs_results, fp_results) = self.epf_functionality(distributionsub_nodes, gatestation_nodes,
                                                          num_samples, epf_sample_df1, G_ep)
        self.set_result_csv_data("sample_failure_state",
                                 fs_results, name=self.get_parameter("result_name") + "_failure_state",
                                 source="dataframe")
        self.set_result_csv_data("failure_probability",
                                 fp_results,
                                 name=self.get_parameter("result_name") + "_failure_probability",
                                 source="dataframe")

        return True

    def epf_functionality(self, distributionsub_nodes, gatestation_nodes, num_samples, epf_sample_df1, G_ep):
        """Run pipeline functionality analysis for multiple pipelines.
        Args:
        Returns:

        """

        # a distance of M denotes disconnection
        M = 9999
        sampcols = ['s' + samp for samp in np.arange(num_samples).astype(str)]

        func_ep_df = pd.DataFrame(np.zeros((len(distributionsub_nodes), num_samples)), index=distributionsub_nodes,
                                  columns=sampcols)

        for si, scol in enumerate(sampcols):
            nodestate_ep = epf_sample_df1.loc[:, ['nodenwid', scol]]
            linkstate_ep = None
            badlinks_ep = EpfFunctionalityUtil.get_bad_edges(G_ep, nodestate_ep, linkstate_ep, scol)
            badlinkdict_ep = {k: {'weight': M} for k in badlinks_ep}
            G1_ep = copy.deepcopy(G_ep)
            nx.set_edge_attributes(G1_ep, badlinkdict_ep)
            res_ep = EpfFunctionalityUtil.network_shortest_paths(G1_ep, gatestation_nodes, distributionsub_nodes)
            func_ep_df.loc[distributionsub_nodes, scol] = (res_ep < M) * 1

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
            ],
            'input_datasets': [
                {
                    'id': 'pipeline_repair_rate_damage',
                    'required': True,
                    'description': 'Output of pipelinedamagerepairrate analysis',
                    'type': ['ergo:pipelineDamageVer3'],
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
