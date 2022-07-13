# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd
import networkx as nx


class EpnFunctionalityUtil:

    @staticmethod
    def get_bad_edges(G, nodestate, linkstate=None, scol='s0'):
        badnodes = nodestate.loc[nodestate.loc[:, scol] == 0, 'nodenwid'].values
        if linkstate is not None:
            badlinks = linkstate.loc[linkstate.loc[:, scol] == 0, ['fromnode', 'tonode']].values
            badlinks = list(zip(badlinks[:, 0], badlinks[:, 1]))
        else:
            badlinks = []
        badlinks2 = list(G.edges(badnodes))
        badlinks.extend(badlinks2)
        return list(set(badlinks))

    @staticmethod
    def network_shortest_paths(G, sources, sinks, weightcol='weight'):
        return pd.Series(nx.multi_source_dijkstra_path_length(G, sources, cutoff=None, weight=weightcol))[sinks]

    @staticmethod
    def gdf_to_nx(gdf_nodes, gdf_edges):
        # generate graph from GeoDataFrame of LineStrings
        net = nx.Graph()
        net.graph['crs'] = gdf_nodes.crs
        node_fields = list(gdf_nodes.columns)
        for index, row in gdf_nodes.iterrows():
            node_data = [row[f] for f in node_fields]
            node_attributes = dict(zip(node_fields, node_data))
            nodeid = row.nodenwid
            net.add_node(nodeid, **node_attributes)
        edge_fields = list(gdf_edges.columns)
        for index, row in gdf_edges.iterrows():
            first = row.fromnode
            last = row.tonode
            edge_data = [row[f] for f in edge_fields]
            edge_attributes = dict(zip(edge_fields, edge_data))
            net.add_edge(first, last, **edge_attributes)
        return net
