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
        """Execute electric power facility functionality analysis"""

        # get network dataset
        network_dataset = NetworkDataset.from_dataset(
            self.get_input_dataset("epn_network")
        )
        links_epl_gdf = network_dataset.links.get_dataframe_from_shapefile()
        nodes_epf_gdf = network_dataset.nodes.get_dataframe_from_shapefile()
        links_epl_gdf["weight"] = links_epl_gdf.loc[:, "length_km"]
        G_ep = network_dataset.get_graph_networkx()

        # get epf sample
        epf_dmg_fs = self.get_input_dataset(
            "epf_sample_failure_state"
        ).get_dataframe_from_csv()
        epf_sample_df = pd.DataFrame(
            np.array(
                [
                    np.array(epf_dmg_fs.failure.values[i].split(",")).astype("int")
                    for i in np.arange(epf_dmg_fs.shape[0])
                ]
            ),
            index=epf_dmg_fs.guid.values,
        )
        # get the sample number
        num_samples = epf_sample_df.shape[1]
        sampcols = ["s" + samp for samp in np.arange(num_samples).astype(str)]

        # add column
        epf_sample_df.columns = sampcols
        epf_sample_df1 = (
            nodes_epf_gdf.loc[:, ["guid", "nodenwid"]]
            .set_index("guid")
            .join(epf_sample_df)
        )

        # get gate station nodes
        gate_station_node_list = self.get_parameter("gate_station_node_list")
        if gate_station_node_list is None:
            # default to EPPL
            gatestation_nodes_class = "EPPL"
            # get the guid from the matching class
            gate_station_node_list = nodes_epf_gdf[
                nodes_epf_gdf["utilfcltyc"] == gatestation_nodes_class
            ]["nodenwid"].to_list()

        # calculate the distribution nodes
        distribution_sub_nodes = list(
            set(list(G_ep.nodes)) - set(gate_station_node_list)
        )

        (fs_results, fp_results) = self.epf_functionality(
            distribution_sub_nodes,
            gate_station_node_list,
            num_samples,
            sampcols,
            epf_sample_df1,
            G_ep,
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

    def epf_functionality(
        self,
        distribution_sub_nodes,
        gate_station_node_list,
        num_samples,
        sampcols,
        epf_sample_df1,
        G_ep,
    ):
        """
        Run EPN functionality analysis.

        Args:
            distribution_sub_nodes (list): distribution nodes
            gate_station_node_list (list): gate station nodes
            num_samples (int): number of simulations
            sampcols (list): list of number samples. e.g. "s0, s1,..."
            epf_sample_df1 (dataframe): epf mcs failure sample dataframe with added field "weight"
            G_ep (networkx object): constructed network

        Returns:
            fs_results (list): A list of dictionary with id/guid and failure state for N samples
            fp_results (list): A list dictionary with failure probability and other data/metadata.

        """

        # a distance of M denotes disconnection
        M = 9999
        func_ep_df = pd.DataFrame(
            np.zeros((len(distribution_sub_nodes), num_samples)),
            index=distribution_sub_nodes,
            columns=sampcols,
        )

        for si, scol in enumerate(sampcols):
            nodestate_ep = epf_sample_df1.loc[:, ["nodenwid", scol]]
            linkstate_ep = None
            badlinks_ep = EpnFunctionalityUtil.get_bad_edges(
                G_ep, nodestate_ep, linkstate_ep, scol
            )
            badlinkdict_ep = {k: {"weight": M} for k in badlinks_ep}
            G1_ep = copy.deepcopy(G_ep)
            nx.set_edge_attributes(G1_ep, badlinkdict_ep)
            res_ep = EpnFunctionalityUtil.network_shortest_paths(
                G1_ep, gate_station_node_list, distribution_sub_nodes
            )
            func_ep_df.loc[distribution_sub_nodes, scol] = (res_ep < M) * 1

        # use nodenwid index to get its guid
        fs_temp = pd.merge(
            func_ep_df,
            epf_sample_df1["nodenwid"],
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
        """Get specifications of the EPN functionality analysis.
        Returns:
            obj: A JSON object of specifications of the EPN functionality analysis.
        """
        return {
            "name": "epn-functionality",
            "description": "electric power network functionality analysis",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "result dataset name",
                    "type": str,
                },
                {
                    "id": "gate_station_node_list",
                    "required": False,
                    "description": "list of gate station nodes",
                    "type": List[int],
                },
            ],
            "input_datasets": [
                {
                    "id": "epn_network",
                    "required": True,
                    "description": "EPN Network Dataset",
                    "type": ["incore:epnNetwork"],
                },
                {
                    "id": "epf_sample_failure_state",
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
