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
    network.add_nodes_from(node_df['Node_ID'])

    # add arcs to the network
    for i in range(len(arc_df)):
        fromnode = arc_df['fromnode'][i]
        tonode = arc_df['tonode'][i]
        dis = arc_df['len_mile'][i]/arc_df['freeflowsd'][i]
        network.add_edge(fromnode, tonode, distance=dis, adt=adt_data[i])

    return network
