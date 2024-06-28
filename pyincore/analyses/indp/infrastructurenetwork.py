# Copyright (c) 2023 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import networkx as nx


class InfrastructureNetwork(object):
    """
    Stores information of the infrastructure network

    Attributes
    ----------
    G : networkx.DiGraph
        The networkx graph object that stores node, arc, and interdependency information
    S : list
        List of geographical spaces on which the network lays
    id : int
        Id of the network
    """

    def __init__(self, id):
        self.G = nx.DiGraph()
        self.S = []
        self.id = id

    def copy(self):
        """
        This function copies the current :class:`InfrastructureNetwork` object

        Returns
        -------
        new_net: :class:`InfrastructureNetwork`
            Copy of the current infrastructure network object
        """
        new_net = InfrastructureNetwork(self.id)
        new_net.G = self.G.copy()
        new_net.S = [s for s in self.S]
        return new_net

    def update_with_strategy(self, player_strategy):
        """
        This function modify the functionality of node and arc per a given strategy

        Parameters
        ----------
        player_strategy : list
            Given strategy, where the first list item shows the functionality of nodes, and the second one is for arcs

        Returns
        -------
        None.

        """
        for q in player_strategy[0]:
            strat = player_strategy[0][q]
            self.G.node[q]["data"]["inf_data"].repaired = round(strat["repair"])
            self.G.node[q]["data"]["inf_data"].functionality = round(strat["w"])
        for q in player_strategy[1]:
            src = q[0]
            dst = q[1]
            strat = player_strategy[1][q]
            self.G[src][dst]["data"]["inf_data"].repaired = round(strat["repair"])
            self.G[src][dst]["data"]["inf_data"].functionality = round(strat["y"])

    def get_clusters(self, layer):
        """
        This function find the clusters in a layer of the network

        Parameters
        ----------
        layer : int
            The id of the desired layer

        Returns
        -------
            : list
            List of layer components

        """
        g_prime_nodes = [
            n[0]
            for n in self.G.nodes(data=True)
            if n[1]["data"]["inf_data"].net_id == layer
            and n[1]["data"]["inf_data"].functionality == 1.0
        ]
        g_prime = nx.DiGraph(self.G.subgraph(g_prime_nodes).copy())
        g_prime.remove_edges_from(
            [
                (u, v)
                for u, v, a in g_prime.edges(data=True)
                if a["data"]["inf_data"].functionality == 0.0
            ]
        )
        # print nx.connected_components(g_prime.to_undirected())
        return list(nx.connected_components(g_prime.to_undirected()))

    def gc_size(self, layer):
        """
        This function finds the size of the largest component in a layer of the network

        Parameters
        ----------
        layer : int
            The id of the desired layer

        Returns
        -------
            : int
            Size of the largest component in the layer
        """
        g_prime_nodes = [
            n[0]
            for n in self.G.nodes(data=True)
            if n[1]["data"]["inf_data"].net_id == layer
            and n[1]["data"]["inf_data"].functionality == 1.0
        ]
        g_prime = nx.Graph(self.G.subgraph(g_prime_nodes))
        g_prime.remove_edges_from(
            [
                (u, v)
                for u, v, a in g_prime.edges(data=True)
                if a["data"]["inf_data"].functionality == 0.0
            ]
        )
        cc = nx.connected_components(g_prime.to_undirected())
        if cc:
            # if len(list(cc)) == 1:
            #    print "I'm here"
            #    return len(list(cc)[0])
            # cc_list=list(cc)
            # print "Length",len(cc_list)
            # if len(cc_list) == 1:
            #    return len(cc_list[0])
            return len(max(cc, key=len))
        else:
            return 0

    def to_game_file(self, layers=None):
        """
        This function writes the multi-defender security games.

        Parameters
        ----------
        layers : list
            List of layers in the game.

        Returns
        -------
        None.

        """
        if layers is None:
            layers = [1, 3]
        with open("../results/indp_gamefile.game") as f:
            num_players = len(layers)
            num_targets = len(
                [
                    n
                    for n in self.G.nodes(data=True)
                    if n[1]["data"]["inf_data"].net_id in layers
                ]
            )
            f.write(str(num_players) + "," + str(num_targets) + ",2\n")
            for layer in range(len(layers)):
                layer_nodes = [
                    n
                    for n in self.G.nodes(data=True)
                    if n[1]["data"]["inf_data"].net_id == layers[layer]
                ]
                for node in layer_nodes:
                    def_values = [0.0] * len(layers)
                    def_values[layer] = abs(node[1]["data"]["inf_data"].demand)
                    atk_values = sum(def_values)
                    f.write(str(layer) + "\n")
                    # f.write("0.0,1.0")
                    for v in def_values:
                        f.write(str(v) + "\n")
                    f.write(str(atk_values) + "\n")

    def to_csv(self, filename="infrastructure_adj.csv"):
        """
        This function writes the object to a csv file

        Parameters
        ----------
        filename : str
            Name of the file to which the network should be written

        Returns
        -------
        None.

        """
        with open(filename, "w") as f:
            for u, v, a in self.G.edges(data=True):
                f.write(
                    str(u[0])
                    + "."
                    + str(u[1])
                    + ","
                    + str(v[0])
                    + "."
                    + str(v[1])
                    + "\n"
                )
