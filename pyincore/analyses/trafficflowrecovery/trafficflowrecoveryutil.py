# Copyright (c) 2018 University of Illinois and others. All rights reserved.

# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from __future__ import division
import csv
import pandas as pd
import networkx as nx
import copy
import math
from pyincore import GeoUtil, InventoryDataset


class TrafficFlowRecoveryUtil:
    @staticmethod
    def NBI_coordinate_mapping(NBI_file):
        """Coordinate in NBI is in format of xx(degree)xx(minutes)xx.xx(seconds)
        map it to traditional xx.xxxx in order to create shapefile.

        Args:
            NBI_file (str): Filename of a NBI file.

        Returns:
            dict: NBI.

        """
        NBI = pd.read_csv(NBI_file)
        NBI["LONG_017"] = NBI["LONG_017"].apply(
            lambda x: -1 * (GeoUtil.degree_to_decimal(x))
        )
        NBI["LAT_016"] = NBI["LAT_016"].apply(lambda x: GeoUtil.degree_to_decimal(x))

        return NBI

    @staticmethod
    def get_average_daily_traffic(bridges, NBI_shapefile):
        NBI = InventoryDataset(NBI_shapefile)
        NBI_features = list(NBI.inventory_set)

        ADT = {}
        for bridge in bridges:
            # convert lon and lat to the right format
            bridge_coord = GeoUtil.get_location(bridge)
            nearest_feature, distance = GeoUtil.find_nearest_feature(
                NBI_features, bridge_coord
            )

            ADT[bridge["properties"]["guid"]] = nearest_feature["properties"]["ADT_029"]

        return ADT

    @staticmethod
    def convert_dmg_prob2state(dmg_results_filename):
        """Upstream bridge damage analysis will generate a dmg result file with the probability
        of each damage state; here determine what state using the maximum probability.

        Args:
            dmg_results_filename (str): Filename of a damage results file.

        Returns:
            dict: Bridge damage values.
            list: Unrepaired bridge.

        """
        bridge_damage_value = {}
        unrepaired_bridge = []

        with open(dmg_results_filename, "r") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                state_id = row[0]
                mean_damage = float(row[10])

                if mean_damage > 0 and mean_damage < 0.25:
                    bridge_damage_value[state_id] = 1
                elif mean_damage >= 0.25 and mean_damage < 0.5:
                    bridge_damage_value[state_id] = 2
                elif mean_damage >= 0.5 and mean_damage < 0.75:
                    bridge_damage_value[state_id] = 3
                elif mean_damage >= 0.75 and mean_damage <= 1:
                    bridge_damage_value[state_id] = 4
                else:
                    raise ValueError("mean damage should not larger than 1!")

            unrepaired_bridge = list(bridge_damage_value.keys())

        return bridge_damage_value, unrepaired_bridge

    @staticmethod
    def nw_reconstruct(node_df, arc_df, adt_data):
        """

        Args:
            node_df (pd.DataFrame): A node in _node_.csv.
            arc_df (pd.DataFrame): A node in edge in _edge_.csv.
            adt_data (pd.DataFrame): Average daily traffic flow.

        Returns:
            obj: Network

        """
        # create network
        network = nx.Graph()

        # add nodes to the network
        network.add_nodes_from(node_df["guid"])

        # add arcs to the network
        for i in range(len(arc_df)):
            fromnode = node_df.loc[
                node_df["ID"] == arc_df["fromnode"][i], "guid"
            ].values[0]
            tonode = node_df.loc[node_df["ID"] == arc_df["tonode"][i], "guid"].values[0]
            dis = arc_df["len_mile"][i] / arc_df["freeflowsp"][i]
            network.add_edge(
                fromnode, tonode, distance=dis, adt=adt_data[arc_df["guid"][i]]
            )

        return network

    @staticmethod
    def traveltime_freeflow(temp_network):
        """A travel time calculation.

        Args:
            temp_network (obj): The investigated network.

        Returns:
            float: Travel efficiency.

        """
        network = copy.deepcopy(temp_network)

        for Ed in temp_network.edges():
            if network.edges[Ed[0], Ed[1]]["Damage_Status"] > 2:
                network.remove_edge(Ed[0], Ed[1])
            elif network.edges[Ed[0], Ed[1]]["Damage_Status"] == 2:
                network.edges[Ed[0], Ed[1]]["distance"] = (
                    network.edges[Ed[0], Ed[1]]["distance"] / 0.5
                )
            elif network.edges[Ed[0], Ed[1]]["Damage_Status"] == 1:
                network.edges[Ed[0], Ed[1]]["distance"] = (
                    network.edges[Ed[0], Ed[1]]["distance"] / 0.75
                )

        num_node = len(network.nodes())
        distance = [[0 for x in range(num_node)] for y in range(num_node)]

        tdistance = dict(nx.all_pairs_dijkstra_path_length(network, weight="distance"))
        i = 0
        for key1, value1 in tdistance.items():
            j = 0
            for key2 in list(value1.keys()):
                distance[i][j] = tdistance[key1][key2]
                j += 1
            i += 1

        travel_efficiency = 0
        for i in range(num_node):
            for j in range(num_node):
                if i != j:
                    if distance[i][j] == 0:
                        distance[i][j] = math.inf
                    travel_efficiency += 1 / distance[i][j]

        return travel_efficiency
