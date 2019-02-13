# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from __future__ import division
import pandas as pd
import copy
import random
import os

from pyincore.analyses.transportationrecovery import freeflow_traveltime as ft
from pyincore.analyses.transportationrecovery.nsga2 import NSGAII
from pyincore.analyses.transportationrecovery import WIPW as WIPW
from pyincore.analyses.transportationrecovery.transportation_recovery_util import TransportationRecoveryUtil
from pyincore.analyses.transportationrecovery.network_reconstruction import nw_reconstruct
from pyincore.analyses.transportationrecovery.post_disaster_long_term_solution import PostDisasterLongTermSolution


class TransportationRecovery:

    def __init__(self, nodes, links, bridges, bridge_damage_value, unrepaired_bridge, ADT):
        
        # read the nodes in transportation
        self.node_df = pd.DataFrame(columns=nodes[0]['properties'].keys())
        for node in nodes:
            self.node_df = self.node_df.append(node['properties'], ignore_index=True)

        # read the link in transportation
        self.arc_df = pd.DataFrame(columns=links[0]['properties'].keys())
        for link in links:
            self.arc_df = self.arc_df.append(link['properties'], ignore_index=True)

        # read bridge information
        self.bridge_df = pd.DataFrame(columns=bridges[0]['properties'].keys())
        for bridge in bridges:
            self.bridge_df = self.bridge_df.append(bridge['properties'], ignore_index=True)

        # read bridge damage information
        self.bridge_damage_value = bridge_damage_value
        self.unrepaired_bridge = unrepaired_bridge

        seed = 333
        random.seed(seed)

        # record the average daily traffic (ADT) data of bridge, a road has the
        # same ADT value as its crossing bridge
        self.adt_data = ADT

        # if there is no bridge across a road, the ADT of the road equals to
        # the maxinum value of ADTs
        for i in range(len(self.arc_df)):
            if self.arc_df["guid"][i] not in list(self.adt_data.keys()):
                self.adt_data[self.arc_df["guid"][i]] = max(ADT.values())

    def calc_recovery_scenario(self, pm, ini_num_population, population_size,
                 num_generation, mutation_rate, crossover_rate):

        """
        calculate the recovery trajectory in each scenario
        :param pm: transportation performance metrics 0: WIPW,  1:Free flow travel time
        :param ini_num_population: 5 or 50
        :param population_size: 3 or 30
        :param num_generation: 2 or 250
        :param mutation_rate: 0.1
        :param crossover_rate:1.0
        :return: none
        """

        # create network
        network = nw_reconstruct(self.node_df, self.arc_df, self.adt_data)

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
                            path_adt[node, pairnode][key] \
                                = WIPW.path_adt_from_edges(network, value)
                            path_adt[pairnode, node][key] \
                                = path_adt[node, pairnode][key]
        else:
            all_ipw = None
            all_ipw_length = None
            path_adt = None

        num_objectives = 2

        # implement NSGA for transportation network post-disaster recovery
        nsga2 = NSGAII(num_objectives, mutation_rate, crossover_rate)

        p = []
        for i in range(ini_num_population):
            p.append(PostDisasterLongTermSolution(self.unrepaired_bridge, self.node_df,
                                                  self.arc_df, self.bridge_df,
                                                  self.bridge_damage_value, network,
                                                  pm, all_ipw, path_adt))

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
            {"Bridge ID": bridge_set, "Ending Time": ending_time})
        fname = 'optimal_solution_of_bridge_repair_schedule.csv'
        TransportationRecoveryUtil.write_output(bridge_recovery, fname)

        network = nw_reconstruct(self.node_df, self.arc_df, self.adt_data)

        temp_bridge_damage_value = copy.deepcopy(self.bridge_damage_value)

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

        # calculate the transportation network efficiency
        efficiency = []
        for ii in range(len(schedule_time)):

            # update the damage status of bridge
            for bridge in bridge_repair:
                if fg[bridge] == 0:
                    if end[bridge] <= schedule_time[ii]:
                        temp_bridge_damage_value[bridge] = 0
                        fg[bridge] = 1

            for i in range(len(self.arc_df)):
                nod1 = self.node_df.loc[self.node_df['ID'] == self.arc_df['fromnode'][i], 'guid'].values[0]
                nod2 = self.node_df.loc[self.node_df['ID'] == self.arc_df['tonode'][i], 'guid'].values[0]
                network.edges[nod1, nod2]['Damage_Status'] = 0

            for key, val in temp_bridge_damage_value.items():
                linknwid = self.bridge_df.loc[self.bridge_df['guid'] == key, 'linkID'].values[0]

                nod_id1 = self.arc_df[self.arc_df['id'] == linknwid]['fromnode'].values[0]
                nod1 = self.node_df.loc[self.node_df['ID'] == nod_id1, 'guid'].values[0]

                nod_id2 = self.arc_df[self.arc_df['id'] == linknwid]['tonode'].values[0]
                nod2 = self.node_df.loc[self.node_df['ID'] == nod_id2, 'guid'].values[0]

                network.edges[nod1, nod2]['Damage_Status'] = val

            # calculate different travel efficiency based on different
            # performance metrics
            if pm == 1:
                current_te = ft.traveltime_freeflow(network)

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
            {"Ending Time": schedule_time, "Travel Efficiency": efficiency})
        fname = 'overall_transportation_recovery_trajectory.csv'
        TransportationRecoveryUtil.write_output(recovery_trajectory, fname)

        return None

