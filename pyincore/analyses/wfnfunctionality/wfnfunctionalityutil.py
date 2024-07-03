# Copyright (c) 2022 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import pandas as pd
import networkx as nx


class WfnFunctionalityUtil:
    @staticmethod
    def get_bad_edges(G, nodestate, linkstate=None, scol="s0"):
        badnodes = nodestate.loc[nodestate.loc[:, scol] == 0, "nodenwid"].values

        if linkstate is not None:
            badlinks = linkstate.loc[
                linkstate.loc[:, scol] == 0, ["fromnode", "tonode"]
            ].values
            badlinks = list(zip(badlinks[:, 0], badlinks[:, 1]))
        else:
            badlinks = []
        badlinks2 = list(G.edges(badnodes))
        badlinks.extend(badlinks2)
        return list(set(badlinks))

    @staticmethod
    def network_shortest_paths(G, sources, sinks, weightcol="weight"):
        return pd.Series(
            nx.multi_source_dijkstra_path_length(
                G, sources, cutoff=None, weight=weightcol
            )
        )[sinks]
