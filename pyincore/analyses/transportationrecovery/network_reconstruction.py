# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import networkx as nx


def nw_reconstruct(node_df, arc_df, adt_data):
    """
    :param node_df: node in _node_.csv
    :param arc_df:  edge in _edge_.csv
    :param adt_data: Average daily traffic flow
    :return: network
    """
    # create network
    network = nx.Graph()

    # add nodes to the network
    network.add_nodes_from(node_df['guid'])

    # add arcs to the network
    for i in range(len(arc_df)):
        fromnode = node_df.loc[node_df['ID']==arc_df['fromnode'][i], 'guid'].values[0]
        tonode = node_df.loc[node_df['ID']==arc_df['tonode'][i], 'guid'].values[0]
        dis = arc_df['len_mile'][i]/arc_df['freeflowsp'][i]
        network.add_edge(fromnode, tonode, distance=dis, adt=adt_data[arc_df['guid'][i]])

    return network
