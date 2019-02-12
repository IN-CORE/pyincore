# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from __future__ import division
import copy
import networkx as nx


def traveltime_freeflow(temp_network):
    """
    travel time calculation
    :param temp_network: the investigated network
    :return: travel efficiency
    """


    network = copy.deepcopy(temp_network)

    for Ed in temp_network.edges():
        if network.edges[Ed[0], Ed[1]]['Damage_Status'] > 2:
            network.remove_edge(Ed[0], Ed[1])
        elif network.edges[Ed[0], Ed[1]]['Damage_Status'] == 2:
            network.edges[Ed[0], Ed[1]]['distance'] \
                = network.edges[Ed[0], Ed[1]]['distance']/0.5
        elif network.edges[Ed[0], Ed[1]]['Damage_Status'] == 1:
            network.edges[Ed[0], Ed[1]]['distance'] \
                = network.edges[Ed[0], Ed[1]]['distance']/0.75

    num_node = len(network.nodes())
    distance = [[0 for x in range(num_node)] for y in range(num_node)]

    tdistance = dict(nx.all_pairs_dijkstra_path_length(network,
                                                       weight='distance'))
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
                    distance[i][j] = float("inf")
                travel_efficiency += 1/distance[i][j]

    return travel_efficiency
