"""
These function compute the change of demand values over time based on population dislocation models for Seaside and
dislocation time model for Lumberton.
"""

import math
import os
import pickle

import numpy as np
import pandas as pd


class DislocationUtil:
    @staticmethod
    def create_dynamic_param(params, pop_dislocation, dt_params, T=1, N=None):
        """
        This function computes the change of demand values over time based on population dislocation models.

        Parameters
        ----------
        params : dict
            Parameters that are needed to run the INDP optimization.
        T : int, optional
            Number of time steps to optimize over. T=1 shows an iINDP analysis, and T>1 shows a td-INDP. The default is
            1.
        N : :class:`~infrastructure.InfrastructureNetwork`
            The object containing the network data.

        Returns
        -------
         dynamic_params : dict
             Dictionary of dynamic demand value for nodes
        """
        dynamic_param_dict = params["DYNAMIC_PARAMS"]
        return_type = dynamic_param_dict["RETURN"]
        dp_dict_col = ["time", "node", "current pop", "total pop"]
        net_names = {"WATER": 1, "GAS": 2, "POWER": 3, "TELECOME": 4}
        dynamic_params = {}

        output_file = (
            dynamic_param_dict["TESTBED"]
            + "_pop_dislocation_demands_"
            + str(params["MAGNITUDE"])
            + "yr.pkl"
        )
        if os.path.exists(output_file):
            print("\nReading from file...")
            with open(output_file, "rb") as f:
                dynamic_params = pickle.load(f)
            return dynamic_params
        for net in dynamic_param_dict["MAPPING"].keys():
            nn = net_names[net]
            mapping_data = dynamic_param_dict["MAPPING"][net]
            dynamic_params[nn] = pd.DataFrame(columns=dp_dict_col)
            if net == "POWER":
                for n, d in N.G.nodes(data=True):
                    if n[1] != nn:
                        continue
                    guid = d["data"]["inf_data"].guid
                    # Find building in the service area of the node/substation
                    try:
                        serv_area = mapping_data[
                            mapping_data["substations_guid"] == guid
                        ]
                    except KeyError:
                        serv_area = mapping_data[mapping_data["node_guid"] == guid]
                    # compute dynamic_params
                    num_dilocated = {t: 0 for t in range(T + 1)}
                    total_pop_node = 0
                    for _, bldg in serv_area.iterrows():
                        try:
                            pop_bldg_dict = pop_dislocation[
                                pop_dislocation["guid"] == bldg["buildings_guid"]
                            ]
                        except KeyError:
                            pop_bldg_dict = pop_dislocation[
                                pop_dislocation["guid"] == bldg["bldg_guid"]
                            ]
                        for _, hh in pop_bldg_dict.iterrows():
                            total_pop_node += (
                                hh["numprec"] if ~np.isnan(hh["numprec"]) else 0
                            )
                            if hh["dislocated"]:
                                # ..todo Lumebrton dislocation time model. Replace with that of Seaside when available
                                return_time = DislocationUtil.disloc_time_mode(
                                    hh, dt_params
                                )
                                for t in range(return_time):
                                    if t <= T and return_type == "step_function":
                                        num_dilocated[t] += (
                                            hh["numprec"]
                                            if ~np.isnan(hh["numprec"])
                                            else 0
                                        )
                                    elif t <= T and return_type == "linear":
                                        pass  # ..todo Add linear return here
                    for t in range(T + 1):
                        values = [
                            t,
                            n[0],
                            total_pop_node - num_dilocated[t],
                            total_pop_node,
                        ]
                        dynamic_params[n[1]] = dynamic_params[n[1]].append(
                            dict(zip(dp_dict_col, values)), ignore_index=True
                        )
            elif net == "WATER":
                node_pop = {}
                for u, v, a in N.G.edges(data=True):
                    if u[1] != nn or v[1] != nn:
                        continue
                    guid = a["data"]["inf_data"].guid
                    # Find building in the service area of the pipe
                    serv_area = mapping_data[mapping_data["edge_guid"] == guid]
                    start_node = u[0]
                    if start_node not in node_pop.keys():
                        node_pop[start_node] = {
                            "total_pop_node": 0,
                            "num_dilocated": {t: 0 for t in range(T + 1)},
                        }
                    end_node = v[0]
                    if end_node not in node_pop.keys():
                        node_pop[end_node] = {
                            "total_pop_node": 0,
                            "num_dilocated": {t: 0 for t in range(T + 1)},
                        }
                    # compute dynamic_params
                    for _, bldg in serv_area.iterrows():
                        pop_bldg_dict = pop_dislocation[
                            pop_dislocation["guid"] == bldg["bldg_guid"]
                        ]
                        for _, hh in pop_bldg_dict.iterrows():
                            # half of the arc's demand is assigned to each node
                            # also, each arc is counted twice both as (u,v) and (v,u)
                            node_pop[start_node]["total_pop_node"] += (
                                hh["numprec"] / 4 if ~np.isnan(hh["numprec"]) else 0
                            )
                            node_pop[end_node]["total_pop_node"] += (
                                hh["numprec"] / 4 if ~np.isnan(hh["numprec"]) else 0
                            )
                            if hh["dislocated"]:
                                # ..todo Lumebrton dislocation time model. Replace with that of Seaside when available
                                return_time = DislocationUtil.disloc_time_mode(
                                    hh, dt_params
                                )
                                for t in range(return_time):
                                    if t <= T and return_type == "step_function":
                                        node_pop[start_node]["num_dilocated"][t] += (
                                            hh["numprec"] / 4
                                            if ~np.isnan(hh["numprec"])
                                            else 0
                                        )
                                        node_pop[end_node]["num_dilocated"][t] += (
                                            hh["numprec"] / 4
                                            if ~np.isnan(hh["numprec"])
                                            else 0
                                        )
                                    elif t <= T and return_type == "linear":
                                        pass  # ..todo Add linear return here
                for n, val in node_pop.items():
                    for t in range(T + 1):
                        values = [
                            t,
                            n,
                            val["total_pop_node"] - val["num_dilocated"][t],
                            val["total_pop_node"],
                        ]
                        dynamic_params[nn] = dynamic_params[nn].append(
                            dict(zip(dp_dict_col, values)), ignore_index=True
                        )
        with open(output_file, "wb") as f:
            pickle.dump(dynamic_params, f)
        return dynamic_params

    @staticmethod
    def disloc_time_mode(household_data, dt_params):
        race_white = 1 if household_data["race"] == 1 else 0
        race_black = 1 if household_data["race"] == 2 else 0
        hispan = household_data["hispan"] if ~np.isnan(household_data["hispan"]) else 0
        # ..todo verify that the explanatory variable correspond to columns in dt_params
        # ..todo Replace random insurance assumption
        linear_term = (
            household_data["DS_0"] * dt_params["DS0"]
            + household_data["DS_1"] * dt_params["DS1"]
            + household_data["DS_2"] * dt_params["DS2"]
            + household_data["DS_3"] * dt_params["DS3"]
            + race_white * dt_params["white"]
            + race_black * dt_params["black"]
            + hispan * dt_params["hispanic"]
            + np.random.choice([0, 1], p=[0.15, 0.85]) * dt_params["insurance"]
        )
        # household_data['randincome']/1000*dt_params['income']+\#!!! income data
        disloc_time = np.exp(linear_term)
        return_time = math.ceil(
            disloc_time / 7
        )  # !!! assuming each time step is one week
        return return_time

    @staticmethod
    def dynamic_parameters(N, original_N, t, dynamic_params):
        for n, d in N.G.nodes(data=True):
            data = dynamic_params[d["data"]["inf_data"].net_id]
            if d["data"]["inf_data"].demand < 0:
                current_pop = data.loc[
                    (data["node"] == n[0]) & (data["time"] == t), "current pop"
                ].iloc[0]
                total_pop = data.loc[
                    (data["node"] == n[0]) & (data["time"] == t), "total pop"
                ].iloc[0]
                original_demand = original_N.G.nodes[n]["data"]["inf_data"].demand
                d["data"]["inf_data"].demand = original_demand * current_pop / total_pop
