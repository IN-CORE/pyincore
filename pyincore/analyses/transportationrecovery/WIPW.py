# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import copy
import networkx as nx


def ipw_search(v, e):
    """
    Indpendent pathway search
    :param v: vertex
    :param e: edge
    :return: path and path length
    """

    g_local = nx.Graph()

    nodelist = copy.deepcopy(v)
    edgeslist = copy.deepcopy(list(e))

    g_local.add_nodes_from(nodelist)
    for headnode, tailnode in edgeslist:
        g_local.add_edge(headnode, tailnode)

    # calculate length of each link which is 1 for all edges
    length = {}

    for (i, j) in edgeslist:
        length[i, j] = 1
        length[j, i] = 1

    # input the intact links information
    nodespair = []
    for i in nodelist:
        for j in nodelist:
            if i != j and (j, i) not in nodespair:
                nodespair.append((i, j))

    degree = {}
    degree_view = g_local.degree(nodelist)
    for pair in degree_view:
        i = pair[0]
        j = pair[1]
        degree[i] = j

    # calculate upper bound
    ub = {}

    # k-th independent path between nodes pair
    ipath = {}

    # the length of kth independent path between node pair
    path_length = {}

    for (w, q) in nodespair:

        # creat a temp list to search path
        temp_edgelist = copy.deepcopy(edgeslist)

        # up bound of possible number of independent paths
        ub[w, q] = min(degree[w], degree[q])
        ipath[w, q] = {}
        path_length[w, q] = {}
        k = 1

        # label whether stop the calculation
        flag = 1
        while flag == 1:
            g_local.clear()
            g_local.add_nodes_from(nodelist)

            for headnode, tailnode in temp_edgelist:
                g_local.add_edge(headnode, tailnode, length=length[headnode,
                                                                   tailnode])

            try:
                temp = copy.deepcopy(nx.shortest_path(g_local,
                                                      source=w,
                                                      target=q,
                                                      weight='length'))
            except nx.NetworkXNoPath as e:
                # print(w,q)
                # print("NetworkXNoPath")
                temp = []

            # if there is a path connecting the source and target,
            # start to calculate IPW
            if temp:

                # find the shortest path
                ipath[w, q][k] = copy.deepcopy(temp)
                path_length[w, q][k] = 0
                ipathtuple = []

                if len(ipath[w, q][k]) == 2:
                    # for the path just has two nodes
                    # (origin and destination)
                    ipathtuple.append((ipath[w, q][k][0],
                                       ipath[w, q][k][1]))
                    path_length[w, q][k] = length[ipath[w, q][k][0],
                                                  ipath[w, q][k][1]]

                else:
                    # for the path has more than two nodes
                    for p in range(0, len(ipath[w, q][k]) - 1):
                        ipathtuple.append((ipath[w, q][k][p],
                                           ipath[w, q][k][p + 1]))

                        path_length[w, q][k] += length[ipath[w, q][k][p],
                                                       ipath[w, q][k][p + 1]]

                # delete edges that used in previous shortest paths
                for (s, t) in ipathtuple:
                    if (s, t) in temp_edgelist:
                        temp_edgelist.remove((s, t))
                        # temp_edgelist.remove((t, s))

                k += 1

            else:
                flag = 0

    return ipath, path_length


def tipw_index(g, l, path_adt):
    """
    caculate the TIPW index of the network
    :param g: graph
    :param l: Indpendent pathway
    :param path_adt: Adt of the path
    :return: TIPW index of the network
    """

    gnodes = g.nodes()

    # compute the normalized ADT
    normal_path_adt = {}
    for key in path_adt.keys():
        normal_path_adt[key] = {}
        for i, j in path_adt[key].items():
            normal_path_adt[key][i] = len(path_adt[key].values()) * j \
                                      / sum(path_adt[key].values())

    # compute the TIPW of node
    node_tipw = {}
    for node in gnodes:
        node_tipw[node] = 0
        for pairnode in gnodes:
            if pairnode != node:
                if (node, pairnode) in l.keys():
                    for key, value in l[node, pairnode].items():
                        node_tipw[node] \
                            += normal_path_adt[node, pairnode][key] \
                               * path_service_level_edges(g, value)
                elif (pairnode, node) in l.keys():
                    for key, value in l[pairnode, node].items():
                        node_tipw[node] \
                            += normal_path_adt[pairnode, node][key] \
                               * path_service_level_edges(g, value)

    # caculate the TIPW index
    tipw_index_val = 0
    for node in gnodes:
        # network IPW
        tipw_index_val \
            += (1 / float(len(gnodes)) * node_tipw[node]) / (len(gnodes) - 1)

    return tipw_index_val


def path_service_level_edges(g, path):
    """
    compute the service level of a path
    :param g: graph
    :param path: path
    :return: service_level
    """

    service_level = 1
    for i in range(len(path) - 1):
        service_level \
            *= (1 - g.edges[path[i], path[i + 1]]['Damage_Status'] / 4.0)
    return service_level


def path_adt_from_edges(g, path):
    """
    compute the reliabity of path from a set of edges
    :param g: graph
    :param path: path
    :return: reliability
    """

    adt = max(nx.get_edge_attributes(g, 'adt').values())
    for i in range(len(path) - 1):
        adt = min(adt, g.edges[path[i], path[i + 1]]['adt'])

    return adt
