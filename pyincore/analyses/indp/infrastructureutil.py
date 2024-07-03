# Copyright (c) 2023 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore.analyses.indp.infrastructurenode import InfrastructureNode
from pyincore.analyses.indp.infrastructurearc import InfrastructureArc
from pyincore.analyses.indp.infrastructureinterdeparc import InfrastructureInterdepArc
from pyincore.analyses.indp.infrastructurenetwork import InfrastructureNetwork


class InfrastructureUtil:
    @staticmethod
    def load_infrastructure_array_format_extended(
        power_nodes,
        power_arcs,
        water_nodes,
        water_arcs,
        interdep,
        cost_scale=1.0,
        extra_commodity=None,
    ):
        """
        This function reads the infrastructure network from file in the extended format

        Args:
            power_nodes:
            power_arcs:
            water_nodes:
            water_arcs:
            interdep:
            cost_scale (float): The factor by which all cost values has to multiplied. The default is 1.0.
            extra_commodity (dict): ( only for extended format of input data) List of extra-commodities in the
            analysis. The default is None, which only considers a main commodity.

        Returns:
            G (class:`~infrastructure.InfrastructureNetwork`): The object containing the network data.

        """
        net_names = {"Water": 1, "Gas": 2, "Power": 3, "Telecommunication": 4}  # !!!
        G = InfrastructureNetwork("Test")
        global_index = 0

        for index, data in enumerate([power_nodes, water_nodes]):
            if index == 0:
                net = net_names["Power"]
            else:
                net = net_names["Water"]
            for v in data.iterrows():
                try:
                    node_id = v[1]["ID"]
                except KeyError:
                    node_id = v[1]["nodenwid"]
                n = InfrastructureNode(global_index, net, int(node_id))
                G.G.add_node((n.local_id, n.net_id), data={"inf_data": n})
                global_index += 1
                node_main_data = G.G.nodes[(n.local_id, n.net_id)]["data"]["inf_data"]
                node_main_data.reconstruction_cost = float(v[1]["q_ds_3"]) * cost_scale
                node_main_data.oversupply_penalty = float(v[1]["Mp"]) * cost_scale
                node_main_data.undersupply_penalty = float(v[1]["Mm"]) * cost_scale
                node_main_data.demand = float(v[1]["Demand"])
                if "guid" in v[1].index.values:
                    node_main_data.guid = v[1]["guid"]
                resource_names = [x for x in list(v[1].index.values) if x[:2] == "p_"]
                if len(resource_names) > 0:
                    n.set_resource_usage(resource_names)
                    for rc in resource_names:
                        n.resource_usage[rc] = v[1][rc]
                else:
                    n.resource_usage["p_"] = 1
                if extra_commodity:
                    n.set_extra_commodity(extra_commodity[net])
                    for layer in extra_commodity[net]:
                        ext_com_data = G.G.nodes[(n.local_id, n.net_id)]["data"][
                            "inf_data"
                        ].extra_com[layer]
                        ext_com_data["oversupply_penalty"] = (
                            float(v[1]["Mp_" + layer]) * cost_scale
                        )
                        ext_com_data["undersupply_penalty"] = (
                            float(v[1]["Mm_" + layer]) * cost_scale
                        )
                        ext_com_data["demand"] = float(v[1]["Demand_" + layer])

        for index, data in enumerate([power_arcs, water_arcs]):
            if index == 0:
                net = net_names["Power"]
            else:
                net = net_names["Water"]
            for v in data.iterrows():
                try:
                    start_id = v[1]["Start Node"]
                    end_id = v[1]["End Node"]
                except KeyError:
                    start_id = v[1]["fromnode"]
                    end_id = v[1]["tonode"]
                for duplicate in range(2):
                    if duplicate == 0:
                        a = InfrastructureArc(int(start_id), int(end_id), net)
                    elif duplicate == 1:
                        a = InfrastructureArc(int(end_id), int(start_id), net)
                    G.G.add_edge(
                        (a.source, a.layer), (a.dest, a.layer), data={"inf_data": a}
                    )
                    arc_main_data = G.G[(a.source, a.layer)][(a.dest, a.layer)]["data"][
                        "inf_data"
                    ]
                    arc_main_data.flow_cost = float(v[1]["c"]) * cost_scale
                    arc_main_data.reconstruction_cost = float(v[1]["f"]) * cost_scale
                    arc_main_data.capacity = float(v[1]["u"])
                    if "guid" in v[1].index.values:
                        arc_main_data.guid = v[1]["guid"]
                    resource_names = [
                        x for x in list(v[1].index.values) if x[:2] == "h_"
                    ]
                    if len(resource_names) > 0:
                        a.set_resource_usage(resource_names)
                        for rc in resource_names:
                            a.resource_usage[rc] = v[1][rc]
                    else:
                        a.resource_usage["h_"] = 1
                    if extra_commodity:
                        a.set_extra_commodity(extra_commodity[net])
                        for layer in extra_commodity[net]:
                            ext_com_data = G.G[(a.source, a.layer)][(a.dest, a.layer)][
                                "data"
                            ]["inf_data"].extra_com[layer]
                            ext_com_data["flow_cost"] = (
                                float(v[1]["c_" + layer]) * cost_scale
                            )

        for v in interdep.iterrows():
            if v[1]["Type"] == "Physical":
                i = int(v[1]["Dependee Node"])
                net_i = net_names[v[1]["Dependee Network"]]
                j = int(v[1]["Depender Node"])
                net_j = net_names[v[1]["Depender Network"]]
                a = InfrastructureInterdepArc(i, j, net_i, net_j, gamma=1.0)
                G.G.add_edge(
                    (a.source, a.source_layer),
                    (a.dest, a.dest_layer),
                    data={"inf_data": a},
                )
                if extra_commodity:
                    a.set_extra_commodity(extra_commodity[net_i])
                    a.set_extra_commodity(extra_commodity[net_j])

        return G

    @staticmethod
    def add_from_csv_failure_scenario(G, sample, initial_node, initial_link):
        """
        This function reads initial damage data from file in the from_csv format, and applies it to the infrastructure
        network. This format only considers one magnitude value (0), and there can be as many samples from that magnitude.

        Parameters
        ----------
        G : :class:`~infrastructure.InfrastructureNetwork`
             The object containing the network data.
        sample : int
            Sample number of the initial damage scenario,

        Returns
        -------
        None.

        """
        for index, row in initial_node.iterrows():
            raw_n = row["name"].split(",")
            n = (int(raw_n[0].strip(" )(")), int(raw_n[1].strip(" )(")))
            state = float(row[sample + 1])
            G.G.nodes[n]["data"]["inf_data"].functionality = state
            G.G.nodes[n]["data"]["inf_data"].repaired = state

        for index, row in initial_link.iterrows():
            raw_uv = row["name"].split(",")
            u = (int(raw_uv[0].strip(" )(")), int(raw_uv[1].strip(" )(")))
            v = (int(raw_uv[2].strip(" )(")), int(raw_uv[3].strip(" )(")))
            state = float(row[sample + 1])
            if state == 0.0:
                G.G[u][v]["data"]["inf_data"].functionality = state
                G.G[u][v]["data"]["inf_data"].repaired = state

                G.G[v][u]["data"]["inf_data"].functionality = state
                G.G[v][u]["data"]["inf_data"].repaired = state
