from __future__ import division
import pandas as pd
import copy
import random
from pyincore.analyses.transportationrecovery import freeflow_traveltime as ft
from pyincore.analyses.transportationrecovery.nsga2 import NSGAII
from pyincore.analyses.transportationrecovery import WIPW as WIPW
from pyincore.analyses.transportationrecovery.write_output import write_output
from pyincore.analyses.transportationrecovery.network_reconstruction import nw_reconstruct
from pyincore.analyses.transportationrecovery.post_disaster_long_term_solution import PostDisasterLongTermSolution
import os
import pathos.multiprocessing as mp
from functools import partial
from pyincore import InsecureIncoreClient

class TransportationRecovery:

    def __init__(self, client, local_data_path, num_workers):
        '''

        :param client:
        :param num_workers:
        '''

        self.num_workders = num_workers
        self.local_data_path = local_data_path

        # read the nodes in transportation
        self.node_df = pd.DataFrame(
            pd.read_csv(os.path.join(local_data_path, '_Nodes_.csv'), header='infer'))

        # read the link in transportation
        self.arc_df = pd.DataFrame(
            pd.read_csv(os.path.join(local_data_path, '_Edges_.csv'), header='infer'))

        # read bridge information
        self.bridge_df = pd.DataFrame(
            pd.read_csv(os.path.join(local_data_path, 'Bridge_Characteristics.csv'),
                        header='infer'))

        # read damage status of bridge in 1000 scenarios
        self.damage_state = pd.DataFrame(
            pd.read_csv(os.path.join(local_data_path, 'Component_Damage_Statuses.csv'),
                        header=None))

        seed = 333
        random.seed(seed)

        # calculate recovery trajectory for each damage state scenario
        self.num_scenarios = len(self.damage_state)

        # record the average daily traffic (ADT) data of bridge, a road has the
        # same ADT value as its crossing bridge
        self.adt_data = {}
        for i in range(len(self.bridge_df)):
            self.adt_data[self.bridge_df['linkid'][i]] = self.bridge_df["ADT"][i]

        # if there is no bridge across a road, the ADT of the road equals to
        # the maxinum value of ADTs
        for i in range(len(self.arc_df)):
            if self.arc_df["linknwid"][i] not in list(self.adt_data.keys()):
                self.adt_data[self.arc_df["linknwid"][i]] = max(self.bridge_df["ADT"])


    def _calc_scenario(self, pm, ini_num_population, population_size,
                 num_generation, mutation_rate, crossover_rate, SS):

        """
        calculate the recovery trajectory in each scenario
        :param SS: the scenario number
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

        # input bridge damage status
        bridge_damage_status = {}

        # determine the bridge need to be repaired
        bridge_damage_value = {}
        unrepaired_bridge = []

        for i in range(len(self.bridge_df)):
            if self.damage_state[i][SS] == 'none':
                bridge_damage_status[i] = 0
            elif self.damage_state[i][SS] == 'slight':
                bridge_damage_status[i] = 1
            elif self.damage_state[i][SS] == 'moderate':
                bridge_damage_status[i] = 2
            elif self.damage_state[i][SS] == 'extensive':
                bridge_damage_status[i] = 3
            else:
                bridge_damage_status[i] = 4

            if bridge_damage_status[i] > 0:
                bridge_damage_value[i] = bridge_damage_status[i]
                unrepaired_bridge.append(i)

        num_objectives = 2

        # implement NSGA for transportation network post-disaster recovery
        nsga2 = NSGAII(num_objectives, mutation_rate, crossover_rate)

        p = []
        for i in range(ini_num_population):
            p.append(PostDisasterLongTermSolution(self.local_data_path, unrepaired_bridge,
                                                  bridge_damage_value, network,
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
        path = 'The_' + str(SS) + \
               "_optimal_solution_of_bridge_repair_schedule.csv"
        write_output(bridge_recovery, path)

        network = nw_reconstruct(self.node_df, self.arc_df, self.adt_data)

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
                nod1 = self.arc_df['fromnode'][i]
                nod2 = self.arc_df['tonode'][i]
                network.edges[nod1, nod2]['Damage_Status'] = 0

            for i, j in temp_bridge_damage_value.items():
                nod1 = self.arc_df['fromnode'][self.bridge_df['linkid'][i]]
                nod2 = self.arc_df['tonode'][self.bridge_df['linkid'][i]]
                network.edges[nod1, nod2]['Damage_Status'] = j

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
            print("Scenario " + str(SS), e)

        # output the recovery trajectory
        recovery_trajectory = pd.DataFrame(
            {"Ending Time": schedule_time, "Travel Efficiency": efficiency})
        path = 'The_' + str(
            SS) + '_Scenario_Overall_Transportation_Recovery_Trajectory.csv'
        write_output(recovery_trajectory, path)

        print("Scenario " + str(SS))

    def calc_recovery(self, pm, ini_num_population=5, population_size=3,
                 num_generation=2, mutation_rate=0.1, crossover_rate=1.0):
        for SS in range(0, self.num_scenarios):
            self._calc_scenario(pm, ini_num_population, population_size,
                 num_generation, mutation_rate, crossover_rate, SS)

    def calc_recovery_multiprocessing(self, pm, ini_num_population=5,
                                      population_size=3,num_generation=2,
                                      mutation_rate=0.1, crossover_rate=1.0):

        p = mp.Pool(self.num_workders)

        func = partial(self._calc_scenario, pm, ini_num_population,
              population_size,num_generation,mutation_rate,crossover_rate)
        p.map(func, range(0, self.num_scenarios))


if __name__ == "__main__":

    cred = None
    client = InsecureIncoreClient(
        "http://incore2-services.ncsa.illinois.edu:8888", 'cwang138')
    local_data_path = '/Users/cwang138/Documents/INCORE-2.0/Data'

    # TODO: how to pass client in? do I save the dataset on dataserver?
    transportation_recovery = TransportationRecovery(client, local_data_path, num_workers=8)

    # non parallel
    '''transportation_recovery.calc_recovery(pm=1, ini_num_population=5,
                                          population_size=3,
                                          num_generation=2,
                                          mutation_rate=0.1,
                                          crossover_rate=1.0)'''
    # parallel
    transportation_recovery.calc_recovery_multiprocessing(pm=1, ini_num_population=5,
                                          population_size=3,
                                          num_generation=2,
                                          mutation_rate=0.1,
                                          crossover_rate=1.0)