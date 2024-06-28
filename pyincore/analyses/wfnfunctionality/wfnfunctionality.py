# Copyright (c) 2022 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import copy
import numpy as np
import pandas as pd
import networkx as nx

from typing import List
from pyincore import BaseAnalysis, NetworkDataset, NetworkUtil
from pyincore.analyses.wfnfunctionality.wfnfunctionalityutil import WfnFunctionalityUtil


class WfnFunctionality(BaseAnalysis):
    """Computes water facility network functionality.

    Args:
        incore_client: Service client with authentication info
    """

    def __init__(self, incore_client):
        super(WfnFunctionality, self).__init__(incore_client)

    def run(self):
        """Execute water facility network functionality analysis"""

        # Obtain tank nodes
        tank_nodes = self.get_parameter("tank_node_list")

        # Obtain pump station nodes
        pumpstation_nodes = self.get_parameter("pumpstation_node_list")

        # Get network dataset
        network_dataset = NetworkDataset.from_dataset(
            self.get_input_dataset("wfn_network")
        )
        edges_wfl_gdf = network_dataset.links.get_dataframe_from_shapefile()

        nodes_wfn_gdf = network_dataset.nodes.get_dataframe_from_shapefile()
        edges_wfl_gdf["weight"] = edges_wfl_gdf.loc[:, "length"]

        G_wfn = network_dataset.get_graph_networkx()

        # network test
        fromnode_fld_name = "fromnode"
        tonode_fld_name = "tonode"
        nodenwid_fld_name = "nodenwid"

        node_id_validation = NetworkUtil.validate_network_node_ids(
            network_dataset, fromnode_fld_name, tonode_fld_name, nodenwid_fld_name
        )

        if node_id_validation is False:
            print("ID in from or to node field doesn't exist in the node dataset")
            return False

        # Get water facility damage states
        wf_dmg_fs = self.get_input_dataset(
            "wf_sample_failure_state"
        ).get_dataframe_from_csv()
        wf_sample_df = pd.DataFrame(
            np.array(
                [
                    np.array(wf_dmg_fs.failure.values[i].split(",")).astype("int")
                    for i in np.arange(wf_dmg_fs.shape[0])
                ]
            ),
            index=wf_dmg_fs.guid.values,
        )

        # Get pipeline damage states
        pp_dmg_fs = self.get_input_dataset(
            "pp_sample_failure_state"
        ).get_dataframe_from_csv()
        pp_sample_df = pd.DataFrame(
            np.array(
                [
                    np.array(pp_dmg_fs.failure.values[i].split(",")).astype("int")
                    for i in np.arange(pp_dmg_fs.shape[0])
                ]
            ),
            index=pp_dmg_fs.guid.values,
        )

        # Get the sample number
        num_samples = wf_sample_df.shape[1]
        sampcols = ["s" + samp for samp in np.arange(num_samples).astype(str)]

        # Compose the corresponding dataframes based on columns for water facilities and pipelines
        wf_sample_df.columns = sampcols
        wf_sample_df1 = (
            nodes_wfn_gdf.loc[:, ["guid", "nodenwid"]]
            .set_index("guid")
            .join(wf_sample_df)
        )
        wf_sample_df1 = wf_sample_df1.fillna(1)

        pp_sample_df.columns = sampcols
        pp_sample_df1 = (
            edges_wfl_gdf.loc[:, ["guid", "fromnode", "tonode"]]
            .set_index("guid")
            .join(pp_sample_df)
        )

        # Obtain distribution nodes based on user input
        distribution_nodes = list(
            set(list(G_wfn.nodes)) - set(tank_nodes) - set(pumpstation_nodes)
        )

        (fs_results, fp_results) = self.wfn_functionality(
            distribution_nodes,
            pumpstation_nodes,
            num_samples,
            sampcols,
            wf_sample_df1,
            pp_sample_df1,
            G_wfn,
        )

        self.set_result_csv_data(
            "sample_failure_state",
            fs_results,
            name=self.get_parameter("result_name") + "_failure_state",
            source="dataframe",
        )
        self.set_result_csv_data(
            "failure_probability",
            fp_results,
            name=self.get_parameter("result_name") + "_failure_probability",
            source="dataframe",
        )

        return True

    def wfn_functionality(
        self,
        distribution_nodes,
        pumpstation_nodes,
        num_samples,
        sampcols,
        wf_sample_df1,
        pp_sample_df1,
        G_wfn,
    ):
        """
        Run Water facility network functionality analysis.

        Args:
            distribution_nodes (list): distribution nodes
            pumpstation_nodes (list): pump station nodes
            num_samples (int): number of simulations
            sampcols (list): list of number samples. e.g. "s0, s1,..."
            wf_sample_df1 (dataframe): water facility mcs failure sample dataframe
            pp_sample_df1 (dataframe): pipeline mcs failure sample dataframe
            G_wfn (networkx object): constructed network

        Returns:
            fs_results (list): A list of dictionary with id/guid and failure state for N samples
            fp_results (list): A list dictionary with failure probability and other data/metadata.

        """

        # a distance of M denotes disconnection
        M = 9999

        func_wf_df = pd.DataFrame(
            np.zeros((len(distribution_nodes), num_samples)),
            index=distribution_nodes,
            columns=sampcols,
        )

        for si, scol in enumerate(sampcols):
            nodestate_wfn = wf_sample_df1.loc[:, ["nodenwid", scol]]
            linkstate_wfn = pp_sample_df1.loc[:, ["fromnode", "tonode", scol]]
            badlinks_wfn = WfnFunctionalityUtil.get_bad_edges(
                G_wfn, nodestate_wfn, linkstate_wfn, scol
            )
            badlinkdict_wfn = {k: {"weight": M} for k in badlinks_wfn}
            G1_wfn = copy.deepcopy(G_wfn)
            nx.set_edge_attributes(G1_wfn, badlinkdict_wfn)
            res_ep = WfnFunctionalityUtil.network_shortest_paths(
                G1_wfn, pumpstation_nodes, distribution_nodes
            )
            func_wf_df.loc[distribution_nodes, scol] = (res_ep < M) * 1

        # Use nodenwid index to get its guid
        func_wf_df.index = func_wf_df.index.map(np.int64)

        fs_temp = pd.merge(
            func_wf_df,
            wf_sample_df1["nodenwid"],
            left_index=True,
            right_on="nodenwid",
            how="left",
        ).drop(columns=["nodenwid"])
        fp_temp = fs_temp.copy(deep=True)

        # shape the dataframe into failure probability and failure samples
        fs_temp["failure"] = fs_temp.astype(str).apply(",".join, axis=1)
        fs_results = fs_temp.filter(["failure"])
        fs_results.reset_index(inplace=True)
        fs_results = fs_results.rename(columns={"index": "guid"})

        # calculate failure probability
        # count of 0s divided by sample size
        fp_temp["failure_probability"] = (
            num_samples - fp_temp.sum(axis=1).astype(int)
        ) / num_samples
        fp_results = fp_temp.filter(["failure_probability"])
        fp_results.reset_index(inplace=True)
        fp_results = fp_results.rename(columns={"index": "guid"})

        return fs_results, fp_results

    def get_spec(self):
        """Get specifications of the water facility network functionality analysis.
        Returns:
            obj: A JSON object of specifications of the WFN functionality analysis.
        """
        return {
            "name": "wfn-functionality",
            "description": "water facility network functionality analysis",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "result dataset name",
                    "type": str,
                },
                {
                    "id": "tank_node_list",
                    "required": True,
                    "description": "list of tank nodes",
                    "type": List[int],
                },
                {
                    "id": "pumpstation_node_list",
                    "required": True,
                    "description": "list of pump station nodes",
                    "type": List[int],
                },
            ],
            "input_datasets": [
                {
                    "id": "wfn_network",
                    "required": True,
                    "description": "Water Facility Network Dataset",
                    "type": ["incore:waterNetwork"],
                },
                {
                    "id": "wf_sample_failure_state",
                    "required": True,
                    "description": "CSV file of failure state for each sample. Output from MCS analysis",
                    "type": ["incore:sampleFailureState"],
                },
                {
                    "id": "pp_sample_failure_state",
                    "required": True,
                    "description": "CSV file of failure state for each sample. Output from MCS analysis",
                    "type": ["incore:sampleFailureState"],
                },
            ],
            "output_datasets": [
                {
                    "id": "failure_probability",
                    "description": "CSV file of failure probability",
                    "type": "incore:failureProbability",
                },
                {
                    "id": "sample_failure_state",
                    "description": "CSV file of failure state for each sample",
                    "type": "incore:sampleFailureState",
                },
            ],
        }
