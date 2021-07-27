# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import copy
import networkx as nx
import random
from pyincore.analyses.transportationrecovery.nsga2 import Solution
from pyincore.analyses.transportationrecovery import WIPW as WIPW
from pyincore.analyses.transportationrecovery.transportationrecoveryutil import TransportationRecoveryUtil


class PostDisasterLongTermSolution(Solution):
    """
    Solution for the post disaster long term recovery function.
    """

    # for repair time of bridge assignment
    # slight damage state
    slightRepair = 0.6
    # moderate damage state
    modRepair = 2.5
    # extensive damage state
    extRepair = 75
    # complete damage state
    compRepair = 230

    def __init__(self, candidates, node_df, arc_df, bridge_df, bridge_damage_value,
                 network, pm, all_ipw, path_adt):
        """
        initialize the chromosomes
        """
        Solution.__init__(self, 2)
        self.candidates = candidates
        self.node_df = node_df
        self.arc_df = arc_df
        self.bridge_df = bridge_df
        self.attributes = [i for i in range(len(self.candidates))]
        self.bridge_damage_value = bridge_damage_value
        self.network = network
        self.pm = pm
        self.all_ipw = all_ipw
        self.path_adt = path_adt

        # random sort the sequence
        random.shuffle(self.attributes)

    def evaluate_solution(self, final):
        """
        Implementation of evaluation for all solutions
        """
        temp_bridge_damage_value = copy.deepcopy(self.bridge_damage_value)

        # input the total number of crew groups repairing the bridge at the
        # same time
        simax = 8

        # determine the bridge schedule sequence for each candidate
        # (Chromosome)
        candidate_schedule = {}
        for i in range(len(self.candidates)):
            candidate_schedule[self.attributes[i]] = self.candidates[i]

        trt = 0
        srt = 0

        start = {}
        end = {}
        schedule_time = []

        l = copy.deepcopy(self.attributes)

        for i in range(len(l)):
            if i <= simax - 1:

                # repair start from time 0
                start[candidate_schedule[i]] = 0.0

                # if damage state of bridge is slight damage, repair time
                # is slightRepair
                if temp_bridge_damage_value[candidate_schedule[i]] == 1:
                    end[candidate_schedule[i]] \
                        = start[candidate_schedule[i]] \
                          + PostDisasterLongTermSolution.slightRepair

                # if damage state of bridge is moderate damage, repair time
                # is modRepair
                elif temp_bridge_damage_value[candidate_schedule[i]] == 2:
                    end[candidate_schedule[i]] \
                        = start[candidate_schedule[i]] \
                          + PostDisasterLongTermSolution.modRepair

                # if damage state of bridge is extensive damage, repair time
                # is extRepair
                elif temp_bridge_damage_value[candidate_schedule[i]] == 3:
                    end[candidate_schedule[i]] \
                        = start[candidate_schedule[i]] \
                          + PostDisasterLongTermSolution.extRepair

                # if damage state of bridge is complete damage, repair time
                # is compRepair
                else:
                    end[candidate_schedule[i]] \
                        = start[candidate_schedule[i]] \
                          + PostDisasterLongTermSolution.compRepair

                # store the ending time
                schedule_time.append(end[candidate_schedule[i]])

                # sort the complete time for scheduled bridges to hold maximum
                # simultaneously intervention
                schedule_time.sort()

            else:
                # the repair time of next bridge will be start from the minimum
                # end time of pre-scheduled bridges
                start[candidate_schedule[i]] = schedule_time.pop(0)

                if temp_bridge_damage_value[candidate_schedule[i]] == 1:
                    end[candidate_schedule[i]] \
                        = start[candidate_schedule[i]] \
                          + PostDisasterLongTermSolution.slightRepair

                elif temp_bridge_damage_value[candidate_schedule[i]] == 2:
                    end[candidate_schedule[i]] \
                        = start[candidate_schedule[i]] \
                          + PostDisasterLongTermSolution.modRepair

                elif temp_bridge_damage_value[candidate_schedule[i]] == 3:
                    end[candidate_schedule[i]] \
                        = start[candidate_schedule[i]] \
                          + PostDisasterLongTermSolution.extRepair

                else:
                    end[candidate_schedule[i]] \
                        = start[candidate_schedule[i]] \
                          + PostDisasterLongTermSolution.compRepair

                schedule_time.append(end[candidate_schedule[i]])
                schedule_time.sort()

        # calculate the total recovery time
        trt += max(end.values())

        # compute the srt under current realization
        schedule_time = []
        pp = list(end.values())
        for i in range(len(pp)):
            if pp[i] not in schedule_time:
                schedule_time.append(pp[i])

        schedule_time = sorted(schedule_time)
        denominator = 0
        numerator = 0

        schedule = {}
        self_candidates = copy.deepcopy(self.candidates)

        # label whether a bridge has been repaired
        fg = {}
        for bridge in self_candidates:
            fg[bridge] = 0

        # to reduce the computation, just the performance at every 8-time
        # steps, you can adjust it
        inte = 1
        pl = len(schedule_time)

        for ii in range(pl % inte - 1 + inte, pl, inte):

            if ii > 0:

                # update the damage status of bridges
                for bridge in self_candidates:
                    if fg[bridge] == 0:
                        if end[bridge] <= schedule_time[ii]:
                            temp_bridge_damage_value[bridge] = 0
                            schedule[bridge] = [start[bridge], end[bridge]]
                            fg[bridge] = 1

                for i in range(len(self.arc_df)):
                    nod1 = self.node_df.loc[self.node_df['ID'] == self.arc_df['fromnode'][i], 'guid'].values[0]
                    nod2 = self.node_df.loc[self.node_df['ID'] == self.arc_df['tonode'][i], 'guid'].values[0]
                    self.network.edges[nod1, nod2]['Damage_Status'] = 0

                for key, val in temp_bridge_damage_value.items():
                    linknwid = self.bridge_df.loc[self.bridge_df['guid'] == key, 'linkID'].values[0]

                    nod_id1 = self.arc_df[self.arc_df['id'] == linknwid]['fromnode'].values[0]
                    nod1 = self.node_df.loc[self.node_df['ID'] == nod_id1, 'guid'].values[0]

                    nod_id2 = self.arc_df[self.arc_df['id'] == linknwid]['tonode'].values[0]
                    nod2 = self.node_df.loc[self.node_df['ID'] == nod_id2, 'guid'].values[0]

                    self.network.edges[nod1, nod2]['Damage_Status'] = val

                nx.get_edge_attributes(self.network, 'Damage_Status')

                # calculate the travel efficiency based on different
                # performance metrics based on travel time
                if self.pm == 1:
                    te = TransportationRecoveryUtil.traveltime_freeflow(self.network)

                # based on WIPW
                elif self.pm == 0:
                    te = WIPW.tipw_index(self.network,
                                         self.all_ipw, self.path_adt)

                numerator += te * schedule_time[ii] * (schedule_time[ii]
                                                       - schedule_time[
                                                           ii - inte])
                aa = te
                denominator += te * (schedule_time[ii]
                                     - schedule_time[ii - inte])

        # calculate the skewness of the recovery trajectory
        try:
            srt += numerator / denominator
        except ZeroDivisionError as e:
            print(e)

        # the first objective assignment
        self.objectives[0] = trt

        # the second objective assignment
        self.objectives[1] = srt

        # repair schedule of bridge assignment
        self.sch[self.objectives[0], self.objectives[1]] = schedule

        if final == 0:
            return self.objectives[0], self.objectives[1]
        else:
            return self.objectives[0], self.objectives[1], \
                   self.sch[self.objectives[0], self.objectives[1]]

    def mutate(self):
        """
        Mutation operator
        """

        # label whether continuous the mutation operator, for each chromosome,
        # it just has one time mutation
        rec = True

        # implementation of mutation
        while rec:
            index1 = random.randint(0, len(self.candidates) - 1)
            index2 = random.randint(0, len(self.candidates) - 1)
            if index1 != index2:
                re = self.attributes[index1]
                self.attributes[index1] = self.attributes[index2]
                self.attributes[index2] = re
                rec = False
