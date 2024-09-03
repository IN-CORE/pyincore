# Copyright (c) 2023 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import copy
import os
import sys
import time

import pandas as pd
import pyomo.environ as pyo
from pyomo.opt import SolverFactory, TerminationCondition
from pyomo.util.infeasible import log_infeasible_constraints

from pyincore import BaseAnalysis, NetworkDataset
from pyincore.analyses.indp.dislocationutils import DislocationUtil
from pyincore.analyses.indp.indpresults import INDPResults
from pyincore.analyses.indp.indputil import INDPUtil
from pyincore.analyses.indp.infrastructureutil import InfrastructureUtil

from pyincore import globals as pyglobals


class INDP(BaseAnalysis):
    """
    This class runs INDP or td-INDP for a given number of time steps and input parameters.This analysis takes a
    decentralized approach to solve the Interdependent Network Design Problem (INDP), a family of
    centralized Mixed-Integer Programming (MIP) models, which find the optimal restoration strategy of disrupted
    networked systems subject to budget and operational constraints.

    Contributors
        | Science: Hesam Talebiyan
        | Implementation: Chen Wang and NCSA IN-CORE Dev Team

    Args:
        incore_client (IncoreClient): Service authentication.
    """

    def __init__(self, incore_client):
        super(INDP, self).__init__(incore_client)

    def run(self):
        # input parameters
        network_type = self.get_parameter("network_type")
        sample_range = self.get_parameter("sample_range")
        MAGS = self.get_parameter("MAGS")
        filter_sce = None
        fail_sce_param = {
            "TYPE": network_type,
            "SAMPLE_RANGE": sample_range,
            "MAGS": MAGS,
            "FILTER_SCE": filter_sce,
        }

        RC = self.get_parameter("RC")
        layers = self.get_parameter("layers")
        method = self.get_parameter("method")

        t_steps = self.get_parameter("t_steps")
        if t_steps is None:
            t_steps = 10

        dynamic_params = None
        dislocation_data_type = self.get_parameter("dislocation_data_type")
        return_model = self.get_parameter("return_model")
        testbed_name = self.get_parameter("testbed_name")

        # more advanced; can hide from user for the first implementation
        # this is for dynamically updating the demands
        bldgs2elec_dataset = self.get_input_dataset("bldgs2elec")
        bldgs2wter_dataset = self.get_input_dataset("bldgs2wter")

        if (
            dislocation_data_type is not None
            and return_model is not None
            and testbed_name is not None
            and bldgs2elec_dataset is not None
            and bldgs2wter_dataset is not None
        ):
            dynamic_params = {
                "TYPE": dislocation_data_type,
                "RETURN": return_model,
                "TESTBED": testbed_name,
                "MAPPING": {
                    "POWER": bldgs2elec_dataset.get_dataframe_from_csv(
                        low_memory=False
                    ),
                    "WATER": bldgs2wter_dataset.get_dataframe_from_csv(
                        low_memory=False
                    ),
                },
            }

        extra_commodity = self.get_parameter("extra_commodity")
        time_resource = self.get_parameter("time_resource")
        if time_resource is None:
            time_resource = True

        # save model or not; default to False
        save_model = self.get_parameter("save_model")
        if save_model is None:
            save_model = False

        action_result, cost_result, runtime_result = self.run_method(
            fail_sce_param,
            RC,
            layers,
            method=method,
            t_steps=t_steps,
            misc={
                "DYNAMIC_PARAMS": dynamic_params,
                "EXTRA_COMMODITY": extra_commodity,
                "TIME_RESOURCE": time_resource,
            },
            save_model=save_model,
        )

        self.set_result_csv_data("action", action_result, name="actions.csv")
        self.set_result_csv_data("cost", cost_result, name="costs.csv")
        self.set_result_csv_data("runtime", runtime_result, name="run_time.csv")

    def run_method(
        self,
        fail_sce_param,
        v_r,
        layers,
        method,
        t_steps=10,
        misc=None,
        save_model=False,
    ):
        """
        This function runs restoration analysis based on INDP or td-INDP for different numbers of resources.

        Args:
            fail_sce_param (dict): information about damage scenarios.
            v_r (list): number of resources, if this is a list of floats, each float is interpreted as a different
            total number of resources, and INDP
            is run given the total number of resources. If this is a list of lists of floats, each list is interpreted
            as fixed upper bounds on the number of resources each layer can use (same for all time steps).
            layers (list): List of layers.
            method (str): Algorithm type.
            t_steps (int): Number of time steps of the analysis.
            misc (dict): A dictionary that contains miscellaneous data needed for the analysis
            save_model (bool): Flag indicates if the model should be saved or not
        Returns:

        """

        # input files
        wf_repair_cost = self.get_input_dataset(
            "wf_repair_cost"
        ).get_dataframe_from_csv(low_memory=False)
        wf_repair_cost["budget"] = wf_repair_cost["budget"].str.split(",")
        wf_repair_cost["repaircost"] = wf_repair_cost["repaircost"].str.split(",")
        epf_repair_cost = self.get_input_dataset(
            "epf_repair_cost"
        ).get_dataframe_from_csv(low_memory=False)
        epf_repair_cost["budget"] = epf_repair_cost["budget"].str.split(",")
        epf_repair_cost["repaircost"] = epf_repair_cost["repaircost"].str.split(",")

        pipeline_restoration_time = self.get_input_dataset(
            "pipeline_restoration_time"
        ).get_dataframe_from_csv(low_memory=False)
        pipeline_repair_cost = self.get_input_dataset(
            "pipeline_repair_cost"
        ).get_dataframe_from_csv(low_memory=False)

        powerline_supply_demand_info = self.get_input_dataset(
            "powerline_supply_demand_info"
        ).get_dataframe_from_csv(low_memory=False)
        epf_supply_demand_info = self.get_input_dataset(
            "epf_supply_demand_info"
        ).get_dataframe_from_csv(low_memory=False)
        power_network = NetworkDataset.from_dataset(
            self.get_input_dataset("power_network")
        )
        power_arcs = power_network.links.get_dataframe_from_shapefile().merge(
            powerline_supply_demand_info, on="guid"
        )
        power_nodes = power_network.nodes.get_dataframe_from_shapefile().merge(
            epf_supply_demand_info, on="guid"
        )

        pipeline_supply_demand_info = self.get_input_dataset(
            "pipeline_supply_demand_info"
        ).get_dataframe_from_csv(low_memory=False)
        wf_supply_demand_info = self.get_input_dataset(
            "wf_supply_demand_info"
        ).get_dataframe_from_csv(low_memory=False)
        water_network = NetworkDataset.from_dataset(
            self.get_input_dataset("water_network")
        )
        water_arcs = water_network.links.get_dataframe_from_shapefile().merge(
            pipeline_supply_demand_info, on="guid"
        )
        water_nodes = water_network.nodes.get_dataframe_from_shapefile()
        water_nodes = water_nodes.merge(wf_supply_demand_info, on="guid")

        interdep = self.get_input_dataset("interdep").get_dataframe_from_csv(
            low_memory=False
        )

        # get rid of distribution nodes
        wf_failure_state_df = (
            self.get_input_dataset("wf_failure_state")
            .get_dataframe_from_csv(low_memory=False)
            .dropna()
        )
        wf_damage_state_df = (
            self.get_input_dataset("wf_damage_state")
            .get_dataframe_from_csv(low_memory=False)
            .dropna()
        )
        pipeline_failure_state_df = (
            self.get_input_dataset("pipeline_failure_state")
            .get_dataframe_from_csv(low_memory=False)
            .dropna()
        )
        epf_failure_state_df = (
            self.get_input_dataset("epf_failure_state")
            .get_dataframe_from_csv(low_memory=False)
            .dropna()
        )
        epf_damage_state_df = (
            self.get_input_dataset("epf_damage_state")
            .get_dataframe_from_csv(low_memory=False)
            .dropna()
        )

        sample_range = self.get_parameter("sample_range")
        initial_node = INDPUtil.generate_intial_node_failure_state(
            wf_failure_state_df,
            epf_failure_state_df,
            water_nodes,
            power_nodes,
            sample_range,
        )
        initial_link = INDPUtil.generate_intial_link_failure_state(
            pipeline_failure_state_df, water_arcs, power_arcs, sample_range
        )

        pop_dislocation = self.get_input_dataset(
            "pop_dislocation"
        ).get_dataframe_from_csv(low_memory=False)

        wf_restoration_time = self.get_input_dataset(
            "wf_restoration_time"
        ).get_dataframe_from_csv(low_memory=False)
        wf_restoration_time = wf_restoration_time.merge(wf_damage_state_df, on="guid")

        epf_restoration_time = self.get_input_dataset(
            "epf_restoration_time"
        ).get_dataframe_from_csv(low_memory=False)
        epf_restoration_time = epf_restoration_time.merge(
            epf_damage_state_df, on="guid"
        )

        dt_params_dataset = self.get_input_dataset("dt_params")
        if dt_params_dataset is not None:
            dt_params = dt_params_dataset.get_json_reader()
        else:
            dt_params = {
                "DS0": 1.00,
                "DS1": 2.33,
                "DS2": 2.49,
                "DS3": 3.62,
                "white": 0.78,
                "black": 0.88,
                "hispanic": 0.83,
                "income": -0.00,
                "insurance": 1.06,
            }

        # results
        action_result = []
        cost_result = []
        runtime_result = []
        for v_i, v in enumerate(v_r):
            if method == "INDP":
                params = {
                    "NUM_ITERATIONS": t_steps,
                    "OUTPUT_DIR": "indp_results",
                    "V": v,
                    "T": 1,
                    "L": layers,
                    "ALGORITHM": "INDP",
                }
            elif method == "TDINDP":
                params = {
                    "NUM_ITERATIONS": t_steps,
                    "OUTPUT_DIR": "tdindp_results",
                    "V": v,
                    "T": t_steps,
                    "L": layers,
                    "ALGORITHM": "INDP",
                }
                if "WINDOW_LENGTH" in misc.keys():
                    params["WINDOW_LENGTH"] = misc["WINDOW_LENGTH"]
            else:
                raise ValueError(
                    "Wrong method name: "
                    + method
                    + ". We currently only support INDP and TDINDP as  "
                    "method name"
                )

            params["EXTRA_COMMODITY"] = misc["EXTRA_COMMODITY"]
            params["TIME_RESOURCE"] = misc["TIME_RESOURCE"]
            params["DYNAMIC_PARAMS"] = misc["DYNAMIC_PARAMS"]
            if misc["DYNAMIC_PARAMS"]:
                params["OUTPUT_DIR"] = "dp_" + params["OUTPUT_DIR"]

            print("----Running for resources: " + str(params["V"]))
            for m in fail_sce_param["MAGS"]:
                for i in fail_sce_param["SAMPLE_RANGE"]:
                    params["SIM_NUMBER"] = i
                    params["MAGNITUDE"] = m

                    print(
                        "---Running Magnitude " + str(m) + " sample " + str(i) + "..."
                    )
                    if params["TIME_RESOURCE"]:
                        print("Computing repair times...")

                        wf_repair_cost_sample = wf_repair_cost.copy()
                        wf_repair_cost_sample["budget"] = wf_repair_cost_sample[
                            "budget"
                        ].apply(lambda x: float(x[i]))
                        wf_repair_cost_sample["repaircost"] = wf_repair_cost_sample[
                            "repaircost"
                        ].apply(lambda x: float(x[i]))

                        epf_repair_cost_sample = epf_repair_cost.copy()
                        epf_repair_cost_sample["budget"] = epf_repair_cost_sample[
                            "budget"
                        ].apply(lambda x: float(x[i]))
                        epf_repair_cost_sample["repaircost"] = epf_repair_cost_sample[
                            "repaircost"
                        ].apply(lambda x: float(x[i]))

                        # logic to read repair time
                        wf_restoration_time_sample = pd.DataFrame()
                        for index, row in wf_restoration_time.iterrows():
                            failure_state = int(
                                row["sample_damage_states"].split(",")[i].split("_")[1]
                            )  # DS_0,1,2,3,4
                            if failure_state == 0:
                                repairtime = 0
                            else:
                                repairtime = row["PF_" + str(failure_state - 1)]
                            wf_restoration_time_sample = pd.concat(
                                [
                                    wf_restoration_time_sample,
                                    pd.DataFrame(
                                        [
                                            {
                                                "guid": row["guid"],
                                                "repairtime": repairtime,
                                            }
                                        ]
                                    ),
                                ],
                                ignore_index=True,
                            )
                        epf_restoration_time_sample = pd.DataFrame()
                        for index, row in epf_restoration_time.iterrows():
                            failure_state = int(
                                row["sample_damage_states"].split(",")[i].split("_")[1]
                            )  # DS_0,1,2,3,4
                            if failure_state == 0:
                                repairtime = 0
                            else:
                                repairtime = row["PF_" + str(failure_state - 1)]
                            epf_restoration_time_sample = pd.concat(
                                [
                                    epf_restoration_time_sample,
                                    pd.DataFrame(
                                        [
                                            {
                                                "guid": row["guid"],
                                                "repairtime": repairtime,
                                            }
                                        ]
                                    ),
                                ],
                                ignore_index=True,
                            )

                        (
                            water_nodes,
                            water_arcs,
                            power_nodes,
                            power_arcs,
                        ) = INDPUtil.time_resource_usage_curves(
                            power_arcs,
                            power_nodes,
                            water_arcs,
                            water_nodes,
                            wf_restoration_time_sample,
                            wf_repair_cost_sample,
                            pipeline_restoration_time,
                            pipeline_repair_cost,
                            epf_restoration_time_sample,
                            epf_repair_cost_sample,
                        )

                    print("Initializing network...")
                    params["N"] = INDPUtil.initialize_network(
                        power_nodes,
                        power_arcs,
                        water_nodes,
                        water_arcs,
                        interdep,
                        extra_commodity=params["EXTRA_COMMODITY"],
                    )

                    if params["DYNAMIC_PARAMS"]:
                        print("Computing dynamic demand based on dislocation data...")
                        dyn_dmnd = DislocationUtil.create_dynamic_param(
                            params,
                            pop_dislocation,
                            dt_params,
                            N=params["N"],
                            T=params["NUM_ITERATIONS"],
                        )
                        params["DYNAMIC_PARAMS"]["DEMAND_DATA"] = dyn_dmnd

                    if fail_sce_param["TYPE"] == "from_csv":
                        InfrastructureUtil.add_from_csv_failure_scenario(
                            params["N"],
                            sample=i,
                            initial_node=initial_node,
                            initial_link=initial_link,
                        )
                    else:
                        raise ValueError("Wrong failure scenario data type.")

                    if params["ALGORITHM"] == "INDP":
                        indp_results = self.run_indp(
                            params,
                            layers=params["L"],
                            controlled_layers=params["L"],
                            T=params["T"],
                            save_model=save_model,
                            print_cmd_line=False,
                            co_location=False,
                        )
                        for t in indp_results.results:
                            actions = indp_results[t]["actions"]
                            costs = indp_results[t]["costs"]
                            runtimes = indp_results[t]["run_time"]
                            for a in actions:
                                action_result.append(
                                    {
                                        "RC": str(v_i),
                                        "layers": "L" + str(len(layers)),
                                        "magnitude": "m" + str(m),
                                        "sample_num": str(i),
                                        "t": str(t),
                                        "action": a,
                                    }
                                )

                            runtime_result.append(
                                {
                                    "RC": str(v_i),
                                    "layers": "L" + str(len(layers)),
                                    "magnitude": "m" + str(m),
                                    "sample_num": str(i),
                                    "t": str(t),
                                    "runtime": runtimes,
                                }
                            )

                            cost_result.append(
                                {
                                    "RC": str(v_i),
                                    "layers": "L" + str(len(layers)),
                                    "magnitude": "m" + str(m),
                                    "sample_num": str(i),
                                    "t": str(t),
                                    "Space Prep": str(costs["Space Prep"]),
                                    "Arc": str(costs["Arc"]),
                                    "Node": str(costs["Node"]),
                                    "Over Supply": str(costs["Over Supply"]),
                                    "Under Supply": str(costs["Under Supply"]),
                                    "Flow": str(costs["Flow"]),
                                    "Total": str(costs["Total"]),
                                    "Under Supply Perc": str(
                                        costs["Under Supply Perc"]
                                    ),
                                }
                            )
                    else:
                        raise ValueError("Wrong algorithm type.")

        return action_result, cost_result, runtime_result

    def run_indp(
        self,
        params,
        layers=None,
        controlled_layers=None,
        functionality=None,
        T=1,
        save=True,
        suffix="",
        forced_actions=False,
        save_model=False,
        print_cmd_line=True,
        co_location=True,
    ):
        """
        This function runs iINDP (T=1) or td-INDP for a given number of time steps and input parameters.

        Args:
            params (dict): Parameters that are needed to run the INDP optimization.
            layers (list): List of layers in the interdependent network. The default is 'None', which sets the list
            to [1, 2, 3].
            controlled_layers (list): List of layers that are included in the analysis. The default is 'None',
            which  sets the list equal to layers.
            functionality (dict): This dictionary is used to assign functionality values elements in the network
            before  the analysis starts. The
            default is 'None'.
            T (int): Number of time steps to optimize over. T=1 shows an iINDP analysis, and T>1 shows a td-INDP.
            The default is 1.
            TODO save & suffice aare not exposed to outside should remove it
            save (bool): If the results should be saved to file. The default is True.
            suffix (str): The suffix that should be added to the output files when saved. The default is ''.

            forced_actions (bool): If True, the optimizer is forced to repair at least one element in each time step.
            The default is False.
            TODO expose this parameter
            save_model (bool): If the optimization model should be saved to file. The default is False.
            TODO expose this parameter
            print_cmd_line (bool): If full information about the analysis should be written to the console. The default
            is True.
            TODO expose this parameter
            co_location (bool): If co-location and geographical interdependency should be considered in the analysis.
            The default is True.

        Returns:
             indp_results (INDPResults): `~indputils.INDPResults` object containing the optimal restoration decisions.

        """
        # Initialize failure scenario.
        global original_N
        if functionality is None:
            functionality = {}
        if layers is None:
            layers = [1, 2, 3]
        if controlled_layers is None:
            controlled_layers = layers

        interdependent_net = params["N"]
        if "NUM_ITERATIONS" not in params:
            params["NUM_ITERATIONS"] = 1

        out_dir_suffix_res = INDPUtil.get_resource_suffix(params)
        indp_results = INDPResults(params["L"])
        if T == 1:
            print("--Running INDP (T=1) or iterative INDP.")
            if print_cmd_line:
                print("Num iters=", params["NUM_ITERATIONS"])

            # Run INDP for 1 time step (original INDP).
            output_dir = (
                params["OUTPUT_DIR"]
                + "_L"
                + str(len(layers))
                + "_m"
                + str(params["MAGNITUDE"])
                + "_v"
                + out_dir_suffix_res
            )
            # Initial calculations.
            if params["DYNAMIC_PARAMS"]:
                original_N = copy.deepcopy(interdependent_net)  # !!! deepcopy
                DislocationUtil.dynamic_parameters(
                    interdependent_net,
                    original_N,
                    0,
                    params["DYNAMIC_PARAMS"]["DEMAND_DATA"],
                )
            v_0 = {x: 0 for x in params["V"].keys()}
            results = self.indp(
                interdependent_net,
                v_0,
                1,
                layers,
                controlled_layers=controlled_layers,
                functionality=functionality,
                co_location=co_location,
            )
            indp_results = results[1]
            if save_model:
                INDPUtil.save_indp_model_to_file(results[0], output_dir + "/Model", 0)
            for i in range(params["NUM_ITERATIONS"]):
                print("-Time Step (iINDP)", i + 1, "/", params["NUM_ITERATIONS"])
                if params["DYNAMIC_PARAMS"]:
                    DislocationUtil.dynamic_parameters(
                        interdependent_net,
                        original_N,
                        i + 1,
                        params["DYNAMIC_PARAMS"]["DEMAND_DATA"],
                    )
                results = self.indp(
                    interdependent_net,
                    params["V"],
                    T,
                    layers,
                    controlled_layers=controlled_layers,
                    co_location=co_location,
                    functionality=functionality,
                )
                indp_results.extend(results[1], t_offset=i + 1)
                if save_model:
                    INDPUtil.save_indp_model_to_file(
                        results[0], output_dir + "/Model", i + 1
                    )
                # Modify network to account for recovery and calculate components.
                INDPUtil.apply_recovery(interdependent_net, indp_results, i + 1)
        else:
            # td-INDP formulations. Includes "DELTA_T" parameter for sliding windows to increase efficiency.
            # Edit 2/8/16: "Sliding window" now overlaps.
            num_time_windows = 1
            time_window_length = T
            if "WINDOW_LENGTH" in params:
                time_window_length = params["WINDOW_LENGTH"]
                num_time_windows = T
            output_dir = (
                params["OUTPUT_DIR"]
                + "_L"
                + str(len(layers))
                + "_m"
                + str(params["MAGNITUDE"])
                + "_v"
                + out_dir_suffix_res
            )

            print(
                "Running td-INDP (T="
                + str(T)
                + ", Window size="
                + str(time_window_length)
                + ")"
            )
            # Initial percolation calculations.
            v_0 = {x: 0 for x in params["V"].keys()}
            results = self.indp(
                interdependent_net,
                v_0,
                1,
                layers,
                controlled_layers=controlled_layers,
                functionality=functionality,
                co_location=co_location,
            )
            indp_results = results[1]
            if save_model:
                INDPUtil.save_indp_model_to_file(results[0], output_dir + "/Model", 0)
            for n in range(num_time_windows):
                print("-Time window (td-INDP)", n + 1, "/", num_time_windows)
                functionality_t = {}
                # Slide functionality matrix according to sliding time window.
                if functionality:
                    for t in functionality:
                        if t in range(n, time_window_length + n + 1):
                            functionality_t[t - n] = functionality[t]
                    if len(functionality_t) < time_window_length + 1:
                        diff = time_window_length + 1 - len(functionality_t)
                        max_t = max(functionality_t.keys())
                        for d in range(diff):
                            functionality_t[max_t + d + 1] = functionality_t[max_t]
                # Run td-INDP.
                results = self.indp(
                    interdependent_net,
                    params["V"],
                    time_window_length + 1,
                    layers,
                    controlled_layers=controlled_layers,
                    functionality=functionality_t,
                    co_location=co_location,
                )
                if save_model:
                    INDPUtil.save_indp_model_to_file(
                        results[0], output_dir + "/Model", n + 1
                    )
                if "WINDOW_LENGTH" in params:
                    indp_results.extend(results[1], t_offset=n + 1, t_start=1, t_end=2)
                    # Modify network for recovery actions and calculate components.
                    INDPUtil.apply_recovery(interdependent_net, results[1], 1)
                else:
                    indp_results.extend(results[1], t_offset=0)
                    for t in range(1, T):
                        # Modify network to account for recovery actions.
                        INDPUtil.apply_recovery(interdependent_net, indp_results, t)
        # Save results of current simulation.
        if save:
            if not os.path.exists(output_dir + "/agents"):
                os.makedirs(output_dir + "/agents")
            indp_results.to_csv_layer(
                output_dir + "/agents", params["SIM_NUMBER"], suffix=suffix
            )

        return indp_results

    def indp(
        self,
        N,
        v_r,
        T=1,
        layers=None,
        controlled_layers=None,
        functionality=None,
        fixed_nodes=None,
        print_cmd=True,
        co_location=True,
    ):
        """
        INDP optimization problem in Pyomo. It also solves td-INDP if T > 1.

        Parameters
        ----------
        N : :class:`~infrastructure.InfrastructureNetwork`
            An InfrastructureNetwork instance.
        v_r : dict
            Dictionary of the number of resources of different types in the analysis.
            If the value is a scalar for a type, it shows the total number of resources of that type for all layers.
            If the value is a list for a type, it shows the total number of resources of that type given to each layer.
        T : int, optional
            Number of time steps to optimize over. T=1 shows an iINDP analysis, and T>1 shows a td-INDP. The default is
            1.
        layers : list, optional
            Layer IDs in N included in the optimization.
        controlled_layers : list, optional
            Layer IDs that can be recovered in this optimization. Used for decentralized optimization. The default is
            None.
        functionality : dict, optional
            Dictionary of nodes to functionality values for non-controlled nodes.
            Used for decentralized optimization. The default is None.
        fixed_nodes : dict, optional
            It fixes the functionality of given elements to a given value. The default is None.
        print_cmd : bool, optional
            If true, analysis information is written to the console. The default is True.
        co_location : bool, optional
            If false, exclude geographical interdependency from the optimization. The default is True.
        Returns
        -------
        : list
        A list of the form ``[m, results]`` for a successful optimization where m is the optimization model and
            results is a :class:`~indputils.INDPResults` object generated using  :func:`collect_results`.
            If :envvar:`solution_pool` is set to a number, the function returns ``[m, results,  sol_pool_results]``
            where `sol_pool_results` is dictionary of solution that should be retrieved from the optimizer in
            addition to the optimal one collected using :func:`collect_solution_pool`.

        """
        if functionality is None:
            functionality = {}
        if layers is None:
            layers = [1, 2, 3]
        if controlled_layers is None:
            controlled_layers = layers

        start_time = time.time()

        m = pyo.ConcreteModel()
        m.T = T
        m.N = N
        m.v_r = v_r
        m.functionality = functionality

        """Sets and Dictionaries"""
        g_prime_nodes = [
            n[0]
            for n in N.G.nodes(data=True)
            if n[1]["data"]["inf_data"].net_id in layers
        ]
        g_prime = N.G.subgraph(g_prime_nodes)
        # Nodes in controlled network.
        m.n_hat_nodes = pyo.Set(
            initialize=[
                n[0]
                for n in g_prime.nodes(data=True)
                if n[1]["data"]["inf_data"].net_id in controlled_layers
            ]
        )
        m.n_hat = g_prime.subgraph(m.n_hat_nodes.ordered_data())
        # Damaged nodes in controlled network.
        m.n_hat_prime_nodes = pyo.Set(
            initialize=[
                n[0]
                for n in m.n_hat.nodes(data=True)
                if n[1]["data"]["inf_data"].repaired == 0.0
            ]
        )
        n_hat_prime = [
            n
            for n in m.n_hat.nodes(data=True)
            if n[1]["data"]["inf_data"].repaired == 0.0
        ]
        # Arcs in controlled network.
        m.a_hat = pyo.Set(
            initialize=[
                (u, v)
                for u, v, a in g_prime.edges(data=True)
                if a["data"]["inf_data"].layer in controlled_layers
            ]
        )
        # Damaged arcs in whole network
        m.a_prime = pyo.Set(
            initialize=[
                (u, v)
                for u, v, a in g_prime.edges(data=True)
                if a["data"]["inf_data"].functionality == 0.0
            ]
        )
        a_prime = [
            (u, v, a)
            for u, v, a in g_prime.edges(data=True)
            if a["data"]["inf_data"].functionality == 0.0
        ]
        # Damaged arcs in controlled network.
        m.a_hat_prime = pyo.Set(
            initialize=[
                (u, v)
                for u, v, _ in a_prime
                if m.n_hat.has_node(u) and m.n_hat.has_node(v)
            ]
        )
        a_hat_prime = [
            (u, v, a)
            for u, v, a in a_prime
            if m.n_hat.has_node(u) and m.n_hat.has_node(v)
        ]
        # Sub-spaces
        m.S = pyo.Set(initialize=N.S)

        # Populate interdependencies. Add nodes to N' if they currently rely on a non-functional node.
        m.interdep_nodes = {}
        for u, v, a in g_prime.edges(data=True):
            if not functionality:
                if (
                    a["data"]["inf_data"].is_interdep
                    and g_prime.nodes[u]["data"]["inf_data"].functionality == 0.0
                ):
                    # print "Dependency edge goes from:",u,"to",v
                    if v not in m.interdep_nodes:
                        m.interdep_nodes[v] = []
                    m.interdep_nodes[v].append((u, a["data"]["inf_data"].gamma))
            else:
                # Should populate m.n_hat with layers that are controlled. Then go through m.n_hat.edges(data=True)
                # to find interdependencies.
                for t in range(T):
                    if t not in m.interdep_nodes:
                        m.interdep_nodes[t] = {}
                    if m.n_hat.has_node(v) and a["data"]["inf_data"].is_interdep:
                        if functionality[t][u] == 0.0:
                            if v not in m.interdep_nodes[t]:
                                m.interdep_nodes[t][v] = []
                            m.interdep_nodes[t][v].append(
                                (u, a["data"]["inf_data"].gamma)
                            )

        """Variables"""
        m.time_step = pyo.Set(initialize=range(T))
        # Add geographical space variables.
        if co_location:
            m.S_ids = pyo.Set(initialize=[s.id for s in m.S.value])
            m.z = pyo.Var(m.S_ids, m.time_step, domain=pyo.Binary)
        # Add functionality binary variables for each node in N'.
        m.w = pyo.Var(m.n_hat_nodes, m.time_step, domain=pyo.Binary)
        if T > 1:
            m.w_tilde = pyo.Var(m.n_hat_nodes, m.time_step, domain=pyo.Binary)
        # Add functionality binary variables for each arc in A'.
        m.y = pyo.Var(m.a_hat_prime, m.time_step, domain=pyo.Binary)
        if T > 1:
            m.y_tilde = pyo.Var(m.a_hat_prime, m.time_step, domain=pyo.Binary)
        # Add variables considering extra commodity in addition to the base one
        node_com_idx = []
        for n, d in m.n_hat.nodes(data=True):
            node_com_idx.append((n, "b"))
            for key, val in d["data"]["inf_data"].extra_com.items():
                node_com_idx.append((n, key))
        arc_com_idx = []
        for u, v, a in m.n_hat.edges(data=True):
            arc_com_idx.append((u, v, "b"))
            for key, val in a["data"]["inf_data"].extra_com.items():
                arc_com_idx.append((u, v, key))
        # Add over/under-supply variables for each node.
        m.delta_p = pyo.Var(node_com_idx, m.time_step, domain=pyo.NonNegativeReals)
        m.delta_m = pyo.Var(node_com_idx, m.time_step, domain=pyo.NonNegativeReals)
        # Add flow variables for each arc. (main commodity)
        m.x = pyo.Var(arc_com_idx, m.time_step, domain=pyo.NonNegativeReals)

        # Fix node values
        if fixed_nodes:
            for key, val in fixed_nodes.items():
                if m.T == 1:
                    m.w[key].fix(val)
                else:
                    m.w_tilde[key].fix(val)

        """Populate objective function"""
        obj_func = 0
        for t in range(m.T):
            if co_location:
                for s in N.S:
                    obj_func += s.cost * m.z[s.id, t]
            for u, v, a in a_hat_prime:
                if T == 1:
                    obj_func += (
                        float(a["data"]["inf_data"].reconstruction_cost) / 2.0
                    ) * m.y[u, v, t]
                else:
                    obj_func += (
                        float(a["data"]["inf_data"].reconstruction_cost) / 2.0
                    ) * m.y_tilde[u, v, t]
            for n, d in n_hat_prime:
                if T == 1:
                    obj_func += d["data"]["inf_data"].reconstruction_cost * m.w[n, t]
                else:
                    obj_func += (
                        d["data"]["inf_data"].reconstruction_cost * m.w_tilde[n, t]
                    )
            for n, d in m.n_hat.nodes(data=True):
                obj_func += (
                    d["data"]["inf_data"].oversupply_penalty * m.delta_p[n, "b", t]
                )
                obj_func += (
                    d["data"]["inf_data"].undersupply_penalty * m.delta_m[n, "b", t]
                )
                for layer, val in d["data"]["inf_data"].extra_com.items():
                    obj_func += val["oversupply_penalty"] * m.delta_p[n, layer, t]
                    obj_func += val["undersupply_penalty"] * m.delta_m[n, layer, t]
            for u, v, a in m.n_hat.edges(data=True):
                obj_func += a["data"]["inf_data"].flow_cost * m.x[u, v, "b", t]
                for layer, val in a["data"]["inf_data"].extra_com.items():
                    obj_func += val["flow_cost"] * m.x[u, v, layer, t]
        m.Obj = pyo.Objective(rule=obj_func, sense=pyo.minimize)

        """Constraints"""
        # Time-dependent constraints.
        if m.T > 1:
            m.initial_state_node = pyo.Constraint(
                m.n_hat_prime_nodes,
                rule=INDPUtil.initial_state_node_rule,
                doc="Initialstate at node",
            )
            m.initial_state_arc = pyo.Constraint(
                m.a_hat_prime,
                rule=INDPUtil.initial_state_arc_rule,
                doc="Initial state at arc",
            )
        m.time_dependent_node = pyo.Constraint(
            m.n_hat_prime_nodes,
            m.time_step,
            rule=INDPUtil.time_dependent_node_rule,
            doc="Time dependent recovery constraint at node",
        )
        m.time_dependent_arc = pyo.Constraint(
            m.a_hat_prime,
            m.time_step,
            rule=INDPUtil.time_dependent_arc_rule,
            doc="Time dependent recovery constraint at arc",
        )
        # Enforce a_i,j to be fixed if a_j,i is fixed (and vice versa).
        m.arc_equality = pyo.Constraint(
            m.a_hat_prime,
            m.time_step,
            rule=INDPUtil.arc_equality_rule,
            doc="Arc reconstruction equality",
        )

        # Conservation of flow constraint. (2) in INDP paper.
        m.flow_conserv_node = pyo.Constraint(
            m.delta_p_index_0,
            m.time_step,
            rule=INDPUtil.flow_conserv_node_rule,
            doc="Flow conservation",
        )
        # Flow functionality constraints.
        m.flow_in_functionality = pyo.Constraint(
            m.a_hat,
            m.time_step,
            rule=INDPUtil.flow_in_functionality_rule,
            doc="Flow In Functionality",
        )
        m.flow_out_functionality = pyo.Constraint(
            m.a_hat,
            m.time_step,
            rule=INDPUtil.flow_out_functionality_rule,
            doc="Flow Out Functionality",
        )
        m.flow_arc_functionality = pyo.Constraint(
            m.a_hat,
            m.time_step,
            rule=INDPUtil.flow_arc_functionality_rule,
            doc="Flow Arc Functionality",
        )
        # Resource availability constraints.
        m.resource = pyo.Constraint(
            list(m.v_r.keys()),
            m.time_step,
            rule=INDPUtil.resource_rule,
            doc="Resource availability",
        )
        # Interdependency constraints
        m.interdependency = pyo.Constraint(
            m.n_hat_nodes,
            m.time_step,
            rule=INDPUtil.interdependency_rule,
            doc="Interdependency",
        )
        # Geographic space constraints
        if co_location:
            m.node_geographic_space = pyo.Constraint(
                m.S_ids,
                m.n_hat_prime_nodes,
                m.time_step,
                rule=INDPUtil.node_geographic_space_rule,
                doc="Node Geographic space",
            )
            m.arc_geographic_space = pyo.Constraint(
                m.S_ids,
                m.a_hat_prime,
                m.time_step,
                rule=INDPUtil.arc_geographic_space_rule,
                doc="Arc Geographic space",
            )

        """Solve"""
        num_cont_vars = len(
            [
                v
                for v in m.component_data_objects(pyo.Var)
                if v.domain == pyo.NonNegativeReals
            ]
        )
        num_integer_vars = len(
            [v for v in m.component_data_objects(pyo.Var) if v.domain == pyo.Binary]
        )

        solver_engine = self.get_parameter("solver_engine")
        if solver_engine is None:
            solver_engine = "scip"

        solver_path = self.get_parameter("solver_path")
        if solver_path is None:
            solver_path = pyglobals.SCIP_PATH

        solver_time_limit = self.get_parameter("solver_time_limit")

        print(
            "Solving... using %s solver (%d cont. vars, %d binary vars)"
            % (solver_engine, num_cont_vars, num_integer_vars)
        )

        if solver_engine == "gurobi":
            solver = SolverFactory(solver_engine, timelimit=solver_time_limit)
        else:
            solver = SolverFactory(
                solver_engine, timelimit=solver_time_limit, executable=solver_path
            )

        solution = solver.solve(m)
        run_time = time.time() - start_time

        # Save results.
        if solution.solver.termination_condition in [
            TerminationCondition.optimal,
            TerminationCondition.maxTimeLimit,
        ]:
            if (
                solution.solver.termination_condition
                == TerminationCondition.maxTimeLimit
            ):
                print(
                    "\nOptimizer time limit, gap = %1.3f\n" % solution.a.solution(0).gap
                )
            results = INDPUtil.collect_results(m, controlled_layers, coloc=co_location)
            results.add_run_time(t, run_time)
            return [m, results]
        else:
            log_infeasible_constraints(m, log_expression=True, log_variables=True)
            if solution.solver.termination_condition == TerminationCondition.infeasible:
                print(
                    solution.solver.termination_condition,
                    ": SOLUTION NOT FOUND. (Check data and/or violated "
                    "constraints in the infeasible_model.log).",
                )
            sys.exit()

    def get_spec(self):
        return {
            "name": "INDP",
            "description": "Interdependent Network Design Problem that models the restoration",
            "input_parameters": [
                {
                    "id": "network_type",
                    "required": True,
                    "description": "type of the network, which is set to `from_csv` for Seaside networks. "
                    "e.g. from_csv, incore",
                    "type": str,
                },
                {
                    "id": "MAGS",
                    "required": True,
                    "description": "sets the earthquake return period.",
                    "type": list,
                },
                {
                    "id": "sample_range",
                    "required": True,
                    "description": "sets the range of sample scenarios to be analyzed",
                    "type": range,
                },
                {
                    "id": "dislocation_data_type",
                    "required": False,
                    "description": "type of the dislocation data.",
                    "type": str,
                },
                {
                    "id": "return_model",
                    "required": False,
                    "description": "type of the model for the return of the dislocated population. "
                    "Options: *step_function* and *linear*.",
                    "type": str,
                },
                {
                    "id": "testbed_name",
                    "required": False,
                    "description": "sets the name of the testbed in analysis",
                    "type": str,
                },
                {
                    "id": "extra_commodity",
                    "required": True,
                    "description": "multi-commodity parameters dict",
                    "type": dict,
                },
                {
                    "id": "RC",
                    "required": True,
                    "description": "list of resource caps or the number of available resources in each step of the "
                    "analysis. Each item of the list is a dictionary whose items show the type of "
                    "resource and the available number of that type of resource. For example: "
                    "* If `network_type`=*from_csv*, you have two options:* if, for example, "
                    '`R_c`= [{"budget": 3}, {"budget": 6}], then the analysis is done for the cases '
                    'when there are 3 and 6 resources available of type "budget" '
                    '(total resource assignment).* if, for example, `R_c`= [{"budget": {1:1, 2:1}}, '
                    '{"budget": {1:1, 2:2}}, {"budget": {1:3, 2:3}}] and given there are 2 layers,'
                    " then the analysis is done for the case where each layer gets 1 resource of "
                    'type "budget", AND the case where layer 1 gets 1 and layer 2 gets 2 resources of '
                    'type "budget", AND the case where each layer gets 3 resources of type '
                    '"budget" (Prescribed resource for each layer).',
                    "type": list,
                },
                {
                    "id": "layers",
                    "required": True,
                    "description": "list of layers in the analysis",
                    "type": list,
                },
                {
                    "id": "method",
                    "required": True,
                    "description": "There are two choices of method: 1. `INDP`: runs Interdependent Network "
                    "Restoration Problem (INDP). 2. `TDINDP`: runs time-dependent INDP (td-INDP).  In "
                    'both cases, if "TIME_RESOURCE" is True, then the repair time for each element '
                    "is considered in devising the restoration plans",
                    "type": str,
                },
                {
                    "id": "t_steps",
                    "required": False,
                    "description": "Number of time steps of the analysis",
                    "type": int,
                },
                {
                    "id": "time_resource",
                    "required": False,
                    "description": "if TIME_RESOURCE is True, then the repair time for each element is "
                    "considered in devising the restoration plans",
                    "type": bool,
                },
                {
                    "id": "save_model",
                    "required": False,
                    "description": "If the optimization model should be saved to file. The default is False.",
                    "type": bool,
                },
                {
                    "id": "solver_engine",
                    "required": False,
                    "description": "Solver to use for optimization model. Such as gurobi/glpk/scip, default to scip.",
                    "type": str,
                },
                {
                    "id": "solver_path",
                    "required": False,
                    "description": "Solver to use for optimization model. Such as gurobi/glpk/scip, default to scip.",
                    "type": str,
                },
                {
                    "id": "solver_time_limit",
                    "required": False,
                    "description": "solver time limit in seconds",
                    "type": int,
                },
            ],
            "input_datasets": [
                {
                    "id": "wf_repair_cost",
                    "required": True,
                    "description": "repair cost for each water facility",
                    "type": ["incore:repairCost"],
                },
                {
                    "id": "wf_restoration_time",
                    "required": True,
                    "description": "recording repair time at certain functionality recovery for each class "
                    "and limit state.",
                    "type": ["incore:waterFacilityRepairTime"],
                },
                {
                    "id": "epf_repair_cost",
                    "required": True,
                    "description": "repair cost for each electric power facility",
                    "type": ["incore:repairCost"],
                },
                {
                    "id": "epf_restoration_time",
                    "required": True,
                    "description": "recording repair time at certain functionality recovery for each class "
                    "and limit state.",
                    "type": ["incore:epfRepairTime"],
                },
                {
                    "id": "pipeline_repair_cost",
                    "required": True,
                    "description": "repair cost for each pipeline",
                    "type": ["incore:pipelineRepairCost"],
                },
                {
                    "id": "pipeline_restoration_time",
                    "required": True,
                    "description": "pipeline restoration times",
                    "type": ["incore:pipelineRestorationVer1"],
                },
                {
                    "id": "power_network",
                    "required": True,
                    "description": "EPN Network Dataset",
                    "type": ["incore:epnNetwork"],
                },
                {
                    "id": "water_network",
                    "required": True,
                    "description": "Water Network Dataset",
                    "type": ["incore:waterNetwork"],
                },
                {
                    "id": "powerline_supply_demand_info",
                    "required": True,
                    "description": "Supply and demand information for powerlines",
                    "type": ["incore:powerLineSupplyDemandInfo"],
                },
                {
                    "id": "epf_supply_demand_info",
                    "required": True,
                    "description": "Supply and demand information for epfs",
                    "type": ["incore:epfSupplyDemandInfo"],
                },
                {
                    "id": "wf_supply_demand_info",
                    "required": True,
                    "description": "Supply and demand information for water facilities",
                    "type": ["incore:waterFacilitySupplyDemandInfo"],
                },
                {
                    "id": "pipeline_supply_demand_info",
                    "required": True,
                    "description": "Supply and demand information for water pipelines",
                    "type": ["incore:pipelineSupplyDemandInfo"],
                },
                {
                    "id": "interdep",
                    "required": True,
                    "description": "Interdepenency between water and electric power facilities",
                    "type": ["incore:interdep"],
                },
                {
                    "id": "wf_failure_state",
                    "required": True,
                    "description": "MCS failure state of water facilities",
                    "type": ["incore:sampleFailureState"],
                },
                {
                    "id": "wf_damage_state",
                    "required": True,
                    "description": "MCS damage state of water facilities",
                    "type": ["incore:sampleDamageState"],
                },
                {
                    "id": "pipeline_failure_state",
                    "required": True,
                    "description": "failure state of pipeline from pipeline functionality",
                    "type": ["incore:sampleFailureState"],
                },
                {
                    "id": "epf_failure_state",
                    "required": True,
                    "description": "MCS failure state of electric power facilities",
                    "type": ["incore:sampleFailureState"],
                },
                {
                    "id": "epf_damage_state",
                    "required": True,
                    "description": "MCS damage state of electric power facilities",
                    "type": ["incore:sampleDamageState"],
                },
                {
                    "id": "dt_params",
                    "required": False,
                    "description": "Parameters for population dislocation time",
                    "type": ["incore:dTParams"],
                },
                {
                    "id": "pop_dislocation",
                    "required": True,
                    "description": "Population dislocation output",
                    "type": ["incore:popDislocation"],
                },
                {
                    "id": "bldgs2elec",
                    "required": False,
                    "description": "relation between building and electric power facility",
                    "type": ["incore:bldgs2elec"],
                },
                {
                    "id": "bldgs2wter",
                    "required": False,
                    "description": "relation between building and water facility",
                    "type": ["incore:bldgs2wter"],
                },
            ],
            "output_datasets": [
                {
                    "id": "action",
                    "parent_type": "",
                    "description": "Restoration action plans",
                    "type": "incore:indpAction",
                },
                {
                    "id": "cost",
                    "parent_type": "",
                    "description": "Restoration cost plans",
                    "type": "incore:indpCost",
                },
                {
                    "id": "runtime",
                    "parent_type": "",
                    "description": "Restoration runtime plans",
                    "type": "incore:indpRuntime",
                },
            ],
        }
