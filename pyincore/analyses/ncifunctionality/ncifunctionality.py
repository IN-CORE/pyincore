# Copyright (c) 2022 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import BaseAnalysis, NetworkDataset
from pyincore.utils.networkutil import NetworkUtil
from typing import List
from scipy import stats
import networkx as nx
import pandas as pd
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
        # Load parameters
        discretized_days = self.get_parameter("discretized_days")

        # Load all dataset-related entities for EPF
        epf_network_dataset = NetworkDataset.from_dataset(
            self.get_input_dataset("epf_network")
        )
        epf_network_nodes = epf_network_dataset.nodes.get_dataframe_from_shapefile()
        epf_network_links = epf_network_dataset.links.get_dataframe_from_shapefile()

        # Load all dataset-related entities for WDS
        wds_network_dataset = NetworkDataset.from_dataset(
            self.get_input_dataset("wds_network")
        )
        wds_network_nodes = wds_network_dataset.nodes.get_dataframe_from_shapefile()
        wds_network_links = wds_network_dataset.links.get_dataframe_from_shapefile()

        # Load network interdependencies
        epf_wds_intdp_table = self.get_input_dataset(
            "epf_wds_intdp_table"
        ).get_dataframe_from_csv()
        wds_epf_intdp_table = self.get_input_dataset(
            "wds_epf_intdp_table"
        ).get_dataframe_from_csv()

        # Load restoration functionality and time results for EPF
        epf_time_results = self.get_input_dataset(
            "epf_time_results"
        ).get_dataframe_from_csv()
        epf_subst_failure_results = self.get_input_dataset(
            "epf_subst_failure_results"
        ).get_dataframe_from_csv()
        epf_inventory_rest_map = self.get_input_dataset(
            "epf_inventory_rest_map"
        ).get_dataframe_from_csv()

        # Load restoration functionality and time results for WDS
        wds_time_results = self.get_input_dataset(
            "wds_time_results"
        ).get_dataframe_from_csv()
        wds_dmg_results = self.get_input_dataset(
            "wds_dmg_results"
        ).get_dataframe_from_csv()
        wds_inventory_rest_map = self.get_input_dataset(
            "wds_inventory_rest_map"
        ).get_dataframe_from_csv()

        # Load limit state probabilities and damage states for each electric power facility
        epf_damage = self.get_input_dataset("epf_damage").get_dataframe_from_csv()

        epf_cascading_functionality = self.nci_functionality(
            discretized_days,
            epf_network_nodes,
            epf_network_links,
            wds_network_nodes,
            wds_network_links,
            epf_wds_intdp_table,
            wds_epf_intdp_table,
            epf_subst_failure_results,
            epf_inventory_rest_map,
            epf_time_results,
            wds_dmg_results,
            wds_inventory_rest_map,
            wds_time_results,
            epf_damage,
        )

        result_name = self.get_parameter("result_name")
        self.set_result_csv_data(
            "epf_cascading_functionality",
            epf_cascading_functionality,
            name=result_name,
            source="dataframe",
        )

        return True

    def nci_functionality(
        self,
        discretized_days,
        epf_network_nodes,
        epf_network_links,
        wds_network_nodes,
        wds_network_links,
        epf_wds_intdp_table,
        wds_epf_intdp_table,
        epf_subst_failure_results,
        epf_inventory_rest_map,
        epf_time_results,
        wds_dmg_results,
        wds_inventory_rest_map,
        wds_time_results,
        epf_damage,
    ):
        """Compute EPF and WDS cascading functionality outcomes

        Args:
            discretized_days (List[int]): a list of discretized days
            epf_network_nodes (pd.DataFrame): network nodes for EPF network
            epf_network_links (pd.DataFrame): network links for EPF network
            wds_network_nodes (pd.DataFrame): network nodes for WDS network
            wds_network_links (pd.DataFrame): network links for WDS network
            epf_wds_intdp_table (pd.DataFrame): mapping from EPF to WDS networks
            wds_epf_intdp_table (pd.DataFrame): mapping from WDS to EPF networks
            epf_subst_failure_results (pd.DataFrame): substation failure results for EPF network
            epf_inventory_rest_map (pd.DataFrame): inventory restoration map for EPF network
            epf_time_results (pd.DataFrame): time results for EPF network
            wds_dmg_results (pd.DataFrame): damage results for WDS network
            wds_inventory_rest_map (pd.DataFrame): inventory restoration map for WDS network
            wds_time_results (pd.DataFrame): time results for WDS network
            epf_damage (pd.DataFrame): limit state probabilities and damage states for each guid

        Returns:
            (pd.DataFrame, pd.DataFrame): results for EPF and WDS networks
        """

        # Compute updated EPF and WDS node information
        efp_nodes_updated = self.update_epf_discretized_func(
            epf_network_nodes,
            epf_subst_failure_results,
            epf_inventory_rest_map,
            epf_time_results,
            epf_damage,
        )

        wds_nodes_updated = self.update_wds_discretized_func(
            wds_network_nodes, wds_dmg_results, wds_inventory_rest_map, wds_time_results
        )

        # Compute updated WDS links
        wds_links_updated = self.update_wds_network_links(wds_network_links)

        # Generate the functionality data
        df_functionality_nodes = pd.concat(
            [efp_nodes_updated, wds_nodes_updated], ignore_index=True
        )

        # Create each individual graph
        g_epf = NetworkUtil.create_network_graph_from_dataframes(
            epf_network_nodes, epf_network_links
        )
        g_wds = NetworkUtil.create_network_graph_from_dataframes(
            wds_network_nodes, wds_links_updated
        )

        # Obtain two graphs for directional interdependencies
        g_epf_wds = NetworkUtil.merge_labeled_networks(
            g_epf, g_wds, epf_wds_intdp_table, directed=True
        )

        # To be implemented in a future release
        # g_wds_epf = NetworkUtil.merge_labeled_networks(g_wds, g_epf, wds_epf_intdp_table, directed=True)

        # Solve the corresponding Leontief problems
        df_epn_func_nodes = self.solve_leontief_equation(
            g_epf_wds, df_functionality_nodes, discretized_days
        )

        # To be implemented in a future release
        # df_wds_func_nodes = self.solve_leontief_equation(g_wds_epf, df_functionality_nodes, discretized_days)

        epn_cascading_functionality = (
            epf_network_nodes[["guid", "geometry"]]
            .merge(df_epn_func_nodes, on="guid", how="left")
            .rename(columns={"guid": "sguid"})
        )

        # To be implemented in a future release
        # wds_cascading_functionality = wds_network_nodes[['guid', 'geometry']].merge(df_wds_func_nodes, on='guid',
        # how='left').rename(columns={'guid': 'sguid'})

        return epn_cascading_functionality

    @staticmethod
    def update_epf_discretized_func(
        epf_nodes,
        epf_subst_failure_results,
        epf_inventory_restoration_map,
        epf_time_results,
        epf_damage,
    ):
        epf_time_results = epf_time_results.loc[
            (epf_time_results["time"] == 1)
            | (epf_time_results["time"] == 3)
            | (epf_time_results["time"] == 7)
            | (epf_time_results["time"] == 30)
            | (epf_time_results["time"] == 90)
        ]
        epf_time_results.insert(
            2, "PF_00", list(np.ones(len(epf_time_results)))
        )  # PF_00, PF_0, PF_1, PF_2, PF_3  ---> DS_0, DS_1, DS_2, DS_3, DS_4

        epf_subst_failure_results = pd.merge(
            epf_damage, epf_subst_failure_results, on="guid", how="outer"
        )

        epf_nodes_updated = pd.merge(
            epf_nodes[["nodenwid", "utilfcltyc", "guid"]],
            epf_subst_failure_results[
                ["guid", "DS_0", "DS_1", "DS_2", "DS_3", "DS_4", "failure_probability"]
            ],
            on="guid",
            how="outer",
        )

        EPPL_restoration_id = list(
            epf_inventory_restoration_map.loc[
                epf_inventory_restoration_map["guid"]
                == epf_nodes_updated.loc[
                    epf_nodes_updated["utilfcltyc"] == "EPPL"
                ].guid.tolist()[0]
            ]["restoration_id"]
        )[0]
        ESS_restoration_id = list(
            set(epf_inventory_restoration_map.restoration_id.unique())
            - set([EPPL_restoration_id])
        )[0]
        df_EPN_node_EPPL = epf_nodes_updated.loc[
            epf_nodes_updated["utilfcltyc"] == "EPPL"
        ]
        df_EPN_node_ESS = epf_nodes_updated.loc[
            epf_nodes_updated["utilfcltyc"] != "EPPL"
        ]
        epf_time_results_EPPL = epf_time_results.loc[
            epf_time_results["restoration_id"] == EPPL_restoration_id
        ][["PF_00", "PF_0", "PF_1", "PF_2", "PF_3"]]
        EPPL_func_df = pd.DataFrame(
            np.dot(
                df_EPN_node_EPPL[["DS_0", "DS_1", "DS_2", "DS_3", "DS_4"]],
                np.array(epf_time_results_EPPL).T,
            ),
            columns=[
                "functionality1",
                "functionality3",
                "functionality7",
                "functionality30",
                "functionality90",
            ],
        )
        EPPL_func_df.insert(0, "guid", list(df_EPN_node_EPPL.guid))
        epf_time_results_ESS = epf_time_results.loc[
            epf_time_results["restoration_id"] == ESS_restoration_id
        ][["PF_00", "PF_0", "PF_1", "PF_2", "PF_3"]]
        ESS_func_df = pd.DataFrame(
            np.dot(
                df_EPN_node_ESS[["DS_0", "DS_1", "DS_2", "DS_3", "DS_4"]],
                np.array(epf_time_results_ESS).T,
            ),
            columns=[
                "functionality1",
                "functionality3",
                "functionality7",
                "functionality30",
                "functionality90",
            ],
        )
        ESS_func_df.insert(0, "guid", list(df_EPN_node_ESS.guid))
        epf_function_df = pd.concat([ESS_func_df, EPPL_func_df], ignore_index=True)
        epf_nodes_updated = pd.merge(epf_nodes_updated, epf_function_df, on="guid")

        return epf_nodes_updated

    @staticmethod
    def update_wds_discretized_func(
        wds_nodes, wds_dmg_results, wds_inventory_restoration_map, wds_time_results
    ):
        wf_time_results = wds_time_results.loc[
            (wds_time_results["time"] == 1)
            | (wds_time_results["time"] == 3)
            | (wds_time_results["time"] == 7)
            | (wds_time_results["time"] == 30)
            | (wds_time_results["time"] == 90)
        ]
        wf_time_results.insert(2, "PF_00", list(np.ones(len(wf_time_results))))

        wds_nodes_updated = pd.merge(
            wds_nodes[["nodenwid", "utilfcltyc", "guid"]],
            wds_dmg_results[["guid", "DS_0", "DS_1", "DS_2", "DS_3", "DS_4"]],
            on="guid",
            how="outer",
        )

        PPPL_restoration_id = list(
            wds_inventory_restoration_map.loc[
                wds_inventory_restoration_map["guid"]
                == wds_nodes_updated.loc[
                    wds_nodes_updated["utilfcltyc"] == "PPPL"
                ].guid.tolist()[0]
            ]["restoration_id"]
        )[0]
        PSTAS_restoration_id = list(
            wds_inventory_restoration_map.loc[
                wds_inventory_restoration_map["guid"]
                == wds_nodes_updated.loc[
                    wds_nodes_updated["utilfcltyc"] == "PSTAS"
                ].guid.tolist()[0]
            ]["restoration_id"]
        )[0]
        df_wds_node_PPPL = wds_nodes_updated.loc[
            wds_nodes_updated["utilfcltyc"] == "PPPL"
        ]
        df_wds_node_PSTAS = wds_nodes_updated.loc[
            wds_nodes_updated["utilfcltyc"] == "PSTAS"
        ]

        wf_time_results_PPPL = wf_time_results.loc[
            wf_time_results["restoration_id"] == PPPL_restoration_id
        ][["PF_00", "PF_0", "PF_1", "PF_2", "PF_3"]]
        PPPL_func_df = pd.DataFrame(
            np.dot(
                df_wds_node_PPPL[["DS_0", "DS_1", "DS_2", "DS_3", "DS_4"]],
                np.array(wf_time_results_PPPL).T,
            ),
            columns=[
                "functionality1",
                "functionality3",
                "functionality7",
                "functionality30",
                "functionality90",
            ],
        )
        PPPL_func_df.insert(0, "guid", list(df_wds_node_PPPL.guid))

        wf_time_results_PSTAS = wf_time_results.loc[
            wf_time_results["restoration_id"] == PSTAS_restoration_id
        ][["PF_00", "PF_0", "PF_1", "PF_2", "PF_3"]]
        PSTAS_func_df = pd.DataFrame(
            np.dot(
                df_wds_node_PSTAS[["DS_0", "DS_1", "DS_2", "DS_3", "DS_4"]],
                np.array(wf_time_results_PSTAS).T,
            ),
            columns=[
                "functionality1",
                "functionality3",
                "functionality7",
                "functionality30",
                "functionality90",
            ],
        )
        PSTAS_func_df.insert(0, "guid", list(df_wds_node_PSTAS.guid))

        wf_function_df = pd.concat([PSTAS_func_df, PPPL_func_df], ignore_index=True)
        wds_nodes_updated = pd.merge(wds_nodes_updated, wf_function_df, on="guid")

        return wds_nodes_updated

    @staticmethod
    def solve_leontief_equation(graph, functionality_nodes, discretized_days):
        """Computes the solution to the Leontief equation for network interdependency given a

        Args:
            graph (networkx object): graph containing the integrated EPN-WDS network
            functionality_nodes (pd.DataFrame): dataframe containing discretized EFP/WDS restoration results
            per node
            discretized_days (list): days used for discretization of restoration analyses

        Returns:
            pd.DataFrame
        """
        # Create a deep copy of the incoming fuctionality results to store new values
        df_functionality_nodes = copy.deepcopy(functionality_nodes)

        # M is computed once and remains common across discretized days
        M = nx.adjacency_matrix(graph).todense()

        for idx in discretized_days:
            u = 1 - df_functionality_nodes[f"functionality{idx}"]
            u = u.to_numpy()
            i = np.identity(len(u))
            q = np.dot(np.linalg.inv(i - M.T), u).tolist()
            df_functionality_nodes[f"func_cascading{idx}"] = [
                0 if i >= 1 else 1 - i for i in q
            ]

        return df_functionality_nodes

    @staticmethod
    def update_wds_network_links(wds_network_links):
        """Update network links with functionality attributes

        Args:
            wds_network_links (pd.DataFrame): WDS network links

        Returns:
            pd.DataFrame

        """
        wds_links = copy.deepcopy(wds_network_links)

        # Use `numpgvrpr` from pipeline damage
        # wds_links = pd.merge(wds_links, pp_dmg_results, on='guid', how='outer')

        # Update values with pgv and pgd calculations
        for idx in wds_links["linknwid"]:
            df = wds_links[wds_links.linknwid.isin([idx])]

            # standard deviation of normal distribution
            sigma = 0.85

            # mean of normal distribution
            mu = np.log(0.1)

            C_pgv = 0.2  # 0.2
            C_pgd = 0.8  # 0.8
            im = (C_pgv * df["numpgvrpr"] + C_pgd * df["numpgdrpr"]).sum() / df[
                "length"
            ].sum()
            SI_break = 1 - stats.lognorm(s=sigma, scale=np.exp(mu)).cdf(im)

            C_pgv = 0.8  # 0.2
            C_pgd = 0.2  # 0.8
            im = (C_pgv * df["numpgvrpr"] + C_pgd * df["numpgdrpr"]).sum() / df[
                "length"
            ].sum()
            SI_leak = 1 - stats.lognorm(s=sigma, scale=np.exp(mu)).cdf(im)

            m = wds_links["linknwid"] == idx
            wds_links.loc[m, ["SI_break_idv"]] = SI_break
            wds_links.loc[m, ["SI_leak__idv"]] = SI_leak

            return wds_links

    def get_spec(self):
        """Get specifications of the network cascading interdependency functionality analysis.
        Returns:
            obj: A JSON object of specifications of the NCI functionality analysis.
        """
        return {
            "name": "network-cascading-interdepedency-functionality",
            "description": "Network cascading interdepedency functionality analysis",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "result dataset name",
                    "type": str,
                },
                {
                    "id": "discretized_days",
                    "required": False,
                    "description": "Discretized days to compute functionality",
                    "type": List[int],
                },
            ],
            "input_datasets": [
                {
                    "id": "epf_network",
                    "required": True,
                    "description": "EPN network",
                    "type": ["incore:epnNetwork"],
                },
                {
                    "id": "wds_network",
                    "required": True,
                    "description": "WDS network",
                    "type": ["incore:waterNetwork"],
                },
                {
                    "id": "epf_wds_intdp_table",
                    "required": True,
                    "description": "Table containing interdependency information from EPN to WDS networks",
                    "type": ["incore:networkInterdependencyTable"],
                },
                {
                    "id": "wds_epf_intdp_table",
                    "required": True,
                    "description": "Table containing interdependency information from WDS to EPF networks",
                    "type": ["incore:networkInterdependencyTable"],
                },
                {
                    "id": "epf_subst_failure_results",
                    "required": True,
                    "description": "EPF substation failure results",
                    "type": ["incore:failureProbability"],
                },
                {
                    "id": "epf_inventory_rest_map",
                    "required": True,
                    "description": "EPF inventory restoration map",
                    "type": ["incore:inventoryRestorationMap"],
                },
                {
                    "id": "epf_time_results",
                    "required": True,
                    "description": "A csv file recording repair time for EPF per class and limit state",
                    "type": ["incore:epfRestorationTime"],
                },
                {
                    "id": "wds_dmg_results",
                    "required": True,
                    "description": "WDS damage results",
                    "type": ["ergo:waterFacilityDamageVer6"],
                },
                {
                    "id": "wds_inventory_rest_map",
                    "required": True,
                    "description": "WDS inventory restoration map",
                    "type": ["incore:inventoryRestorationMap"],
                },
                {
                    "id": "wds_time_results",
                    "required": True,
                    "description": "A csv file recording repair time for WDS per class and limit state",
                    "type": ["incore:waterFacilityRestorationTime"],
                },
                {
                    "id": "epf_damage",
                    "required": True,
                    "description": "A csv file with limit state probabilities and damage states for each electric power facility",
                    "type": ["incore:epfDamageVer3"],
                },
            ],
            "output_datasets": [
                {
                    "id": "epf_cascading_functionality",
                    "description": "CSV file of interdependent cascading network functionality for EPF",
                    "type": "incore:epfDiscretizedCascadingFunc",
                }
            ],
        }
