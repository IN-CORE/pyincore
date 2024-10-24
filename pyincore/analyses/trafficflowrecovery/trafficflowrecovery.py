# Copyright (c) 2018 University of Illinois and others. All rights reserved.

# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from __future__ import division
import pandas as pd
import copy
import random

from pyincore.analyses.trafficflowrecovery.trafficflowrecoveryutil import (
    TrafficFlowRecoveryUtil,
)
from pyincore.analyses.trafficflowrecovery.nsga2 import NSGAII
from pyincore.analyses.trafficflowrecovery import WIPW as WIPW
from pyincore.analyses.trafficflowrecovery.post_disaster_long_term_solution import (
    PostDisasterLongTermSolution,
)
from pyincore import BaseAnalysis


class TrafficFlowRecovery(BaseAnalysis):
    def run(self):
        """Executes traffic flow recovery analysis"""

        # read the nodes in traffic flow
        node_set = self.get_input_dataset("nodes").get_inventory_reader()
        nodes = list(node_set)
        node_df = pd.DataFrame(columns=nodes[0]["properties"].keys())
        for node in nodes:
            node_properties_df = pd.DataFrame.from_dict(
                node["properties"], orient="index"
            ).T
            node_df = pd.concat([node_df, node_properties_df], ignore_index=True)

        # read the link in traffic flow
        link_set = self.get_input_dataset("links").get_inventory_reader()
        links = list(link_set)
        arc_df = pd.DataFrame(columns=links[0]["properties"].keys())
        for link in links:
            link_properties_df = pd.DataFrame.from_dict(
                link["properties"], orient="index"
            ).T
            arc_df = pd.concat([arc_df, link_properties_df], ignore_index=True)

        # read bridge information
        bridge_set = self.get_input_dataset("bridges").get_inventory_reader()
        bridges = list(bridge_set)
        bridge_df = pd.DataFrame(columns=bridges[0]["properties"].keys())
        for bridge in bridges:
            bridge_properties_df = pd.DataFrame.from_dict(
                bridge["properties"], orient="index"
            ).T
            bridge_df = pd.concat([bridge_df, bridge_properties_df], ignore_index=True)

        # read bridge damage information
        bridge_damage_value = self.get_input_dataset(
            "bridge_damage_value"
        ).get_json_reader()
        unrepaired_bridge = self.get_input_dataset(
            "unrepaired_bridge"
        ).get_json_reader()

        seed = 333
        random.seed(seed)

        # record the average daily traffic (ADT) data of bridge, a road has the
        # same ADT value as its crossing bridge
        adt_data = self.get_input_dataset("ADT").get_json_reader()
        ADT = copy.deepcopy(adt_data)

        # if there is no bridge across a road, the ADT of the road equals to
        # the maximum value of ADTs
        for i in range(len(arc_df)):
            if arc_df["guid"][i] not in list(adt_data.keys()):
                adt_data[arc_df["guid"][i]] = max(ADT.values())

        pm = self.get_parameter("pm")
        ini_num_population = self.get_parameter("ini_num_population")
        population_size = self.get_parameter("population_size")
        num_generation = self.get_parameter("num_generation")
        mutation_rate = self.get_parameter("mutation_rate")
        crossover_rate = self.get_parameter("crossover_rate")

        # create network
        network = TrafficFlowRecoveryUtil.nw_reconstruct(node_df, arc_df, adt_data)

        if pm == 0:
            # calculate the WIPW (Weighted independent pathways) index
            all_ipw, all_ipw_length = WIPW.ipw_search(network.nodes(), network.edges())
            # Calculate the ADT for each path
            path_adt = {}
            for node in range(len(network.nodes()) - 1):
                for pairnode in range(node + 1, len(network.nodes())):
                    if (node, pairnode) in all_ipw.keys():
                        path_adt[node, pairnode] = {}
                        path_adt[pairnode, node] = {}
                        for key, value in all_ipw[node, pairnode].items():
                            path_adt[node, pairnode][key] = WIPW.path_adt_from_edges(
                                network, value
                            )
                            path_adt[pairnode, node][key] = path_adt[node, pairnode][
                                key
                            ]
        else:
            all_ipw = None
            path_adt = None

        num_objectives = 2

        # implement NSGA for traffic flow network post-disaster recovery
        nsga2 = NSGAII(num_objectives, mutation_rate, crossover_rate)

        p = []
        for i in range(ini_num_population):
            p.append(
                PostDisasterLongTermSolution(
                    unrepaired_bridge,
                    node_df,
                    arc_df,
                    bridge_df,
                    bridge_damage_value,
                    network,
                    pm,
                    all_ipw,
                    path_adt,
                )
            )

        first_front = nsga2.run(p, population_size, num_generation)

        # output the NSGA result
        order = len(first_front) - 1
        obj0 = first_front[order].objectives[0]
        obj1 = first_front[order].objectives[1]
        repair_schedule = first_front[order].sch[obj0, obj1]

        # extract the time just finishing repairing a bridge
        ending_time = []
        bridge_set = []
        for key, value in repair_schedule.items():
            bridge_set.append(key)
            ending_time.append(value[1])

        # output the optimal solution of bridge repair schedule based on NSGA
        bridge_recovery = pd.DataFrame(
            {"Bridge ID": bridge_set, "Ending Time": ending_time}
        )
        self.set_result_csv_data(
            "optimal_solution_of_bridge_repair_schedule",
            bridge_recovery,
            name="optimal_solution_of_bridge_repair_schedule",
            source="dataframe",
        )

        network = TrafficFlowRecoveryUtil.nw_reconstruct(node_df, arc_df, adt_data)

        temp_bridge_damage_value = copy.deepcopy(bridge_damage_value)

        # record the  non-recurrence ending time of bridges
        schedule_time = []
        end = {}
        for key, value in repair_schedule.items():
            if value[1] not in schedule_time:
                schedule_time.append(value[1])
            end[key] = value[1]
        schedule_time.sort()

        # label whether the bridge has been repaired
        bridge_repair = list(repair_schedule.keys())
        fg = {}
        for bridge in bridge_repair:
            fg[bridge] = 0

        # calculate the traffic flow network efficiency
        efficiency = []
        for ii in range(len(schedule_time)):
            # update the damage status of bridge
            for bridge in bridge_repair:
                if fg[bridge] == 0:
                    if end[bridge] <= schedule_time[ii]:
                        temp_bridge_damage_value[bridge] = 0
                        fg[bridge] = 1

            for i in range(len(arc_df)):
                nod1 = node_df.loc[
                    node_df["ID"] == arc_df["fromnode"][i], "guid"
                ].values[0]
                nod2 = node_df.loc[node_df["ID"] == arc_df["tonode"][i], "guid"].values[
                    0
                ]
                network.edges[nod1, nod2]["Damage_Status"] = 0

            for key, val in temp_bridge_damage_value.items():
                linknwid = bridge_df.loc[bridge_df["guid"] == key, "linkID"].values[0]

                nod_id1 = arc_df[arc_df["id"] == linknwid]["fromnode"].values[0]
                nod1 = node_df.loc[node_df["ID"] == nod_id1, "guid"].values[0]

                nod_id2 = arc_df[arc_df["id"] == linknwid]["tonode"].values[0]
                nod2 = node_df.loc[node_df["ID"] == nod_id2, "guid"].values[0]

                network.edges[nod1, nod2]["Damage_Status"] = val

            # calculate different travel efficiency based on different
            # performance metrics
            current_te = None
            if pm == 1:
                current_te = TrafficFlowRecoveryUtil.traveltime_freeflow(network)

            elif pm == 0:
                current_te = WIPW.tipw_index(network, all_ipw, path_adt)

            efficiency.append(current_te)

        # normalize the efficiency at each time of repairing a bridge
        try:
            maxe = max(efficiency)
            for i in range(len(efficiency)):
                efficiency[i] = efficiency[i] / maxe
        except ValueError as e:
            print(e)

        # output the recovery trajectory
        recovery_trajectory = pd.DataFrame(
            {"Ending Time": schedule_time, "Travel Efficiency": efficiency}
        )
        self.set_result_csv_data(
            "overall_traffic_flow_recovery_trajectory",
            recovery_trajectory,
            name="overall_traffic_flow_recovery_trajectory",
            source="dataframe",
        )

        return None

    def get_spec(self):
        """Get specifications of the traffic flow recovery model.

        Returns:
            obj: A JSON object of specifications of the traffic flow recovery model.

        """
        return {
            "name": "traffic-flow-recovery",
            "description": "traffic flow recovery model",
            "input_parameters": [
                {
                    "id": "num_cpu",
                    "required": False,
                    "description": "If using parallel execution, the number of cpus to request",
                    "type": int,
                },
                {
                    "id": "pm",
                    "required": True,
                    "description": "traffic flow performance metrics 0: WIPW,  1:Free flow travel time",
                    "type": int,
                },
                {
                    "id": "ini_num_population",
                    "required": True,
                    "description": "ini_num_population: 5 or 50",
                    "type": int,
                },
                {
                    "id": "population_size",
                    "required": True,
                    "description": "population_size: 3 or 30",
                    "type": int,
                },
                {
                    "id": "num_generation",
                    "required": True,
                    "description": "num_generation: 2 or 250",
                    "type": int,
                },
                {
                    "id": "mutation_rate",
                    "required": True,
                    "description": "0.1",
                    "type": float,
                },
                {
                    "id": "crossover_rate",
                    "required": True,
                    "description": "1.0",
                    "type": float,
                },
            ],
            "input_datasets": [
                {
                    "id": "nodes",
                    "required": True,
                    "description": "road nodes",
                    "type": ["ergo:roadNetwork"],
                },
                {
                    "id": "links",
                    "required": True,
                    "description": "road links",
                    "type": ["ergo:roadNetwork"],
                },
                {
                    "id": "bridges",
                    "required": True,
                    "description": "bridges",
                    "type": ["ergo:bridges", "ergo:bridgesVer2", "ergo:bridgesVer3"],
                },
                {
                    "id": "bridge_damage_value",
                    "required": True,
                    "description": "",
                    "type": ["incore:bridgeDamageValue"],
                },
                {
                    "id": "unrepaired_bridge",
                    "required": True,
                    "description": "",
                    "type": ["incore:unrepairedBridge"],
                },
                {
                    "id": "ADT",
                    "required": True,
                    "description": "",
                    "type": ["incore:ADT"],
                },
            ],
            "output_datasets": [
                {
                    "id": "optimal_solution_of_bridge_repair_schedule",
                    "description": "List the Bridge id and its ending repair time.",
                    "type": "incore:transportationRepairSchedule",
                },
                {
                    "id": "overall_traffic_flow_recovery_trajectory",
                    "description": "shows the overall recovery trajectory of the "
                    + "traffic flow system. List the ending time and "
                    + "travel efficiency for the whole network.",
                    "type": "incore:trafficFlowRecovery",
                },
            ],
        }
