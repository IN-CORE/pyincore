# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import copy
import os
import time

from gurobipy import GRB, Model, LinExpr

from pyincore import BaseAnalysis
from pyincore.analyses.indp.dislocationutils import DislocationUtil
from pyincore.analyses.indp.indpcomponents import INDPComponents
from pyincore.analyses.indp.indpresults import INDPResults
from pyincore.analyses.indp.indputil import INDPUtil
from pyincore.analyses.indp.infrastructureutil import InfrastructureUtil


class INDP(BaseAnalysis):

    def __init__(self, incore_client):
        super(INDP, self).__init__(incore_client)

    def run(self):
        # input parameters
        network_type = self.get_parameter("network_type")
        sample_range = self.get_parameter("sample_range")
        MAGS = self.get_parameter("MAGS")
        filter_sce = None
        fail_sce_param = {
            'TYPE': network_type,
            'SAMPLE_RANGE': sample_range,
            'MAGS': MAGS,
            'FILTER_SCE': filter_sce,
        }

        RC = self.get_parameter('RC')
        layers = self.get_parameter('layers')
        method = self.get_parameter('method')

        t_steps = self.get_parameter('t_steps')
        if t_steps is None:
            t_steps = 10

        dislocation_data_type = self.get_parameter("dislocation_data_type")
        return_model = self.get_parameter("return")
        testbed_name = self.get_parameter("testbed_name")
        dynamic_params = {
            "TYPE": dislocation_data_type,
            "RETURN": return_model,
            "TESTBED": testbed_name,
        }

        extra_commodity = self.get_parameter("extra_commodity")
        time_resource = self.get_parameter("time_resource")
        if time_resource is None:
            time_resource = True

        self.run_method(fail_sce_param, RC, layers, method=method, t_steps=t_steps,
                        misc={'DYNAMIC_PARAMS': dynamic_params,
                              'EXTRA_COMMODITY': extra_commodity,
                              'TIME_RESOURCE': time_resource})

    def run_method(self, fail_sce_param, v_r, layers, method, t_steps=10, misc=None):
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

        Returns:

        """

        for v in v_r:
            if method == 'INDP':
                params = {"NUM_ITERATIONS": t_steps, "OUTPUT_DIR": 'indp_results', "V": v,
                          "T": 1, 'L': layers, "ALGORITHM": "INDP"}
            elif method == 'TDINDP':
                params = {"OUTPUT_DIR": 'tdindp_results', "V": v, "T": t_steps, 'L': layers,
                          "ALGORITHM": "INDP"}
                if 'WINDOW_LENGTH' in misc.keys():
                    params["WINDOW_LENGTH"] = misc['WINDOW_LENGTH']
            else:
                raise ValueError('Wrong method name: ' + method + '. We currently only support INDP and TDINDP as  '
                                                                  'method name')

            params['EXTRA_COMMODITY'] = misc['EXTRA_COMMODITY']
            params['TIME_RESOURCE'] = misc['TIME_RESOURCE']
            params['DYNAMIC_PARAMS'] = misc['DYNAMIC_PARAMS']
            if misc['DYNAMIC_PARAMS']:
                params['OUTPUT_DIR'] = 'dp_' + params['OUTPUT_DIR']

            self.batch_run(params, fail_sce_param)

    def batch_run(self, params, fail_sce_param):
        """
        Batch run different methods for a given list of damage scenarios,
        given global parameters.

        Args:
            params (dict): Parameters that are needed to run the INDP optimization.
            fail_sce_param (dict): Parameters concerning the failure scenarios.

        Returns:

        """
        # input files
        nodes_reptime_func = self.get_input_dataset("nodes_reptime_func").get_dataframe_from_csv(low_memory=False)
        nodes_damge_ratio = self.get_input_dataset("nodes_damge_ratio").get_dataframe_from_csv(low_memory=False)
        arcs_reptime_func = self.get_input_dataset("arcs_reptime_func").get_dataframe_from_csv(low_memory=False)
        arcs_damge_ratio = self.get_input_dataset("arcs_damge_ratio").get_dataframe_from_csv(low_memory=False)
        dmg_sce_data = self.get_input_dataset("dmg_sce_data").get_dataframe_from_csv(low_memory=False)
        power_arcs = self.get_input_dataset("power_arcs").get_dataframe_from_csv(low_memory=False)
        power_nodes = self.get_input_dataset("power_nodes").get_dataframe_from_csv(low_memory=False)
        water_arcs = self.get_input_dataset("water_arcs").get_dataframe_from_csv(low_memory=False)
        water_nodes = self.get_input_dataset("water_nodes").get_dataframe_from_csv(low_memory=False)
        pipeline_dmg = self.get_input_dataset("pipeline_dmg").get_dataframe_from_csv(low_memory=False)
        arcs_damge_ratio = self.get_input_dataset("arcs_damge_ratio").get_dataframe_from_csv(low_memory=False)
        interdep = self.get_input_dataset("interdep").get_dataframe_from_csv(low_memory=False)

        initial_node = self.get_input_dataset("initial_node").get_csv_reader()
        initial_link = self.get_input_dataset("initial_link").get_csv_reader()

        pop_dislocation = self.get_input_dataset("pop_dislocation").get_dataframe_from_csv(low_memeory=False)

        print('----Running for resources: ' + str(params['V']))
        for m in fail_sce_param['MAGS']:
            for i in fail_sce_param['SAMPLE_RANGE']:
                params["SIM_NUMBER"] = i
                params["MAGNITUDE"] = m

                print('---Running Magnitude ' + str(m) + ' sample ' + str(i) + '...')
                if params['TIME_RESOURCE']:
                    print('Computing repair times...')
                    water_nodes, water_arcs, power_nodes, power_arcs =\
                        INDPUtil.time_resource_usage_curves(power_arcs, power_nodes, water_arcs, water_nodes,
                                                            pipeline_dmg, nodes_reptime_func, nodes_damge_ratio,
                                                            arcs_reptime_func, arcs_damge_ratio, dmg_sce_data, i)

                print("Initializing network...")
                params["N"] = INDPUtil.initialize_network(power_nodes, power_arcs, water_nodes, water_arcs, interdep,
                                                          extra_commodity=params["EXTRA_COMMODITY"])

                if params['DYNAMIC_PARAMS']:
                    print("Computing dynamic demand based on dislocation data...")
                    dyn_dmnd = DislocationUtil.create_dynamic_param(params, pop_dislocation, N=params["N"],
                                                                    T=params["NUM_ITERATIONS"])
                    params['DYNAMIC_PARAMS']['DEMAND_DATA'] = dyn_dmnd

                if fail_sce_param['TYPE'] == 'from_csv':
                    InfrastructureUtil.add_from_csv_failure_scenario(params["N"], sample=i, initial_node=initial_node,
                                                                     initial_link=initial_link)
                else:
                    raise ValueError('Wrong failure scenario data type.')

                if params["ALGORITHM"] == "INDP":
                    self.run_indp(params, layers=params['L'], controlled_layers=params['L'], T=params["T"],
                                  save_model=False, print_cmd_line=False, co_location=False)
                else:
                    raise ValueError('Wrong algorithm type.')

    def run_indp(self, params, layers=None, controlled_layers=None, functionality=None, T=1, save=True, suffix="",
                 forced_actions=False, save_model=False, print_cmd_line=True, co_location=True):
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
            save_model (bool): If the Gurobi optimization model should be saved to file. The default is False.
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
            output_dir = params["OUTPUT_DIR"] + '_L' + str(len(layers)) + '_m' + str(
                params["MAGNITUDE"]) + "_v" + out_dir_suffix_res
            # Initial calculations.
            if params['DYNAMIC_PARAMS']:
                original_N = copy.deepcopy(interdependent_net)  # !!! deepcopy
                DislocationUtil.dynamic_parameters(interdependent_net, original_N, 0,
                                                   params['DYNAMIC_PARAMS']['DEMAND_DATA'])
            v_0 = {x: 0 for x in params["V"].keys()}
            results = self.indp(interdependent_net, v_0, 1, layers, controlled_layers=controlled_layers,
                                functionality=functionality, co_location=co_location)
            indp_results = results[1]
            indp_results.add_components(0, INDPComponents.calculate_components(results[0], interdependent_net,
                                                                               layers=controlled_layers))
            for i in range(params["NUM_ITERATIONS"]):
                print("-Time Step (iINDP)", i + 1, "/", params["NUM_ITERATIONS"])
                if params['DYNAMIC_PARAMS']:
                    DislocationUtil.dynamic_parameters(interdependent_net, original_N, i + 1,
                                                       params['DYNAMIC_PARAMS']['DEMAND_DATA'])
                results = self.indp(interdependent_net, params["V"], T, layers, controlled_layers=controlled_layers,
                                    forced_actions=forced_actions, co_location=co_location)
                indp_results.extend(results[1], t_offset=i + 1)
                if save_model:
                    INDPUtil.save_indp_model_to_file(results[0], output_dir + "/Model", i + 1)
                # Modify network to account for recovery and calculate components.
                INDPUtil.apply_recovery(interdependent_net, indp_results, i + 1)
                indp_results.add_components(i + 1, INDPComponents.calculate_components(results[0], interdependent_net,
                                                                                       layers=controlled_layers))
        else:
            # td-INDP formulations. Includes "DELTA_T" parameter for sliding windows to increase efficiency.
            # Edit 2/8/16: "Sliding window" now overlaps.
            num_time_windows = 1
            time_window_length = T
            if "WINDOW_LENGTH" in params:
                time_window_length = params["WINDOW_LENGTH"]
                num_time_windows = T
            output_dir = params["OUTPUT_DIR"] + '_L' + str(len(layers)) + "_m" + str(
                params["MAGNITUDE"]) + "_v" + out_dir_suffix_res

            print("Running td-INDP (T=" + str(T) + ", Window size=" + str(time_window_length) + ")")
            # Initial percolation calculations.
            v_0 = {x: 0 for x in params["V"].keys()}
            results = self.indp(interdependent_net, v_0, 1, layers, controlled_layers=controlled_layers,
                                functionality=functionality, co_location=co_location)
            indp_results = results[1]
            indp_results.add_components(0, INDPComponents.calculate_components(results[0], interdependent_net,
                                                                               layers=controlled_layers))
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
                results = self.indp(interdependent_net, params["V"], time_window_length + 1, layers,
                                    controlled_layers=controlled_layers, functionality=functionality_t,
                                    forced_actions=forced_actions, co_location=co_location)
                if save_model:
                    INDPUtil.save_indp_model_to_file(results[0], output_dir + "/Model", n + 1)
                if "WINDOW_LENGTH" in params:
                    indp_results.extend(results[1], t_offset=n + 1, t_start=1, t_end=2)
                    # Modify network for recovery actions and calculate components.
                    INDPUtil.apply_recovery(interdependent_net, results[1], 1)
                    indp_results.add_components(n + 1,
                                                INDPComponents.calculate_components(results[0], interdependent_net,
                                                                                    1, layers=controlled_layers))
                else:
                    indp_results.extend(results[1], t_offset=0)
                    for t in range(1, T):
                        # Modify network to account for recovery actions.
                        INDPUtil.apply_recovery(interdependent_net, indp_results, t)
                        indp_results.add_components(1,
                                                    INDPComponents.calculate_components(results[0], interdependent_net,
                                                                                        t, layers=controlled_layers))
        # Save results of current simulation.
        if save:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            indp_results.to_csv(output_dir, params["SIM_NUMBER"], suffix=suffix)
            if not os.path.exists(output_dir + '/agents'):
                os.makedirs(output_dir + '/agents')
            indp_results.to_csv_layer(output_dir + '/agents', params["SIM_NUMBER"], suffix=suffix)
        return indp_results

    def indp(self, N, v_r, T=1, layers=None, controlled_layers=None, functionality=None, forced_actions=False,
             fixed_nodes=None, print_cmd=True, time_limit=None, co_location=True, solution_pool=None):
        """
        INDP optimization problem. It also solves td-INDP if T > 1.

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
        forced_actions : bool, optional
            If true, it forces the optimizer to repair at least one element. The default is False.
        fixed_nodes : dict, optional
            It fixes the functionality of given elements to a given value. The default is None.
        print_cmd : bool, optional
            If true, analysis information is written to the console. The default is True.
        time_limit : int, optional
            Time limit for the optimizer to stop. The default is None.
        co_location : bool, optional
            If false, exclude geographical interdependency from the optimization. The default is True.
        solution_pool : int, optional
            The number of solutions that should be retrieved from the optimizer in addition to the optimal one.
            The default is None.

        Returns
        -------
        : list
        A list of the form ``[m, results]`` for a successful optimization where m is the Gurobi  optimization model and
            results is a :class:`~indputils.INDPResults` object generated using  :func:`collect_results`.
            If :envvar:`solution_pool` is set to a number, the function returns ``[m, results,  sol_pool_results]``
            where `sol_pool_results` is dictionary of solution that should be retrieved from the optimizer in
            addition to the optimal one collected using :func:`collect_solution_pool`.

        """
        if fixed_nodes is None:
            fixed_nodes = {}
        if functionality is None:
            functionality = {}
        if layers is None:
            layers = [1, 2, 3]
        if controlled_layers is None:
            controlled_layers = layers

        start_time = time.time()
        m = Model('indp')
        m.setParam('OutputFlag', False)
        if time_limit:
            m.setParam('TimeLimit', time_limit)
        g_prime_nodes = [n[0] for n in N.G.nodes(data=True) if n[1]['data']['inf_data'].net_id in layers]
        g_prime = N.G.subgraph(g_prime_nodes)
        # Damaged nodes in whole network
        n_prime = [n for n in g_prime.nodes(data=True) if n[1]['data']['inf_data'].repaired == 0.0]
        # Nodes in controlled network.
        n_hat_nodes = [n[0] for n in g_prime.nodes(data=True) if n[1]['data']['inf_data'].net_id in controlled_layers]
        n_hat = g_prime.subgraph(n_hat_nodes)
        # Damaged nodes in controlled network.
        n_hat_prime = [n for n in n_hat.nodes(data=True) if n[1]['data']['inf_data'].repaired == 0.0]
        # Damaged arcs in whole network
        a_prime = [(u, v, a) for u, v, a in g_prime.edges(data=True) if a['data']['inf_data'].functionality == 0.0]
        # Damaged arcs in controlled network.
        a_hat_prime = [(u, v, a) for u, v, a in a_prime if n_hat.has_node(u) and n_hat.has_node(v)]
        S = N.S
        # Populate interdependencies. Add nodes to N' if they currently rely on a non-functional node.
        interdep_nodes = {}
        for u, v, a in g_prime.edges(data=True):
            if not functionality:
                if a['data']['inf_data'].is_interdep and g_prime.nodes[u]['data']['inf_data'].functionality == 0.0:
                    # print "Dependency edge goes from:",u,"to",v
                    if v not in interdep_nodes:
                        interdep_nodes[v] = []
                    interdep_nodes[v].append((u, a['data']['inf_data'].gamma))
            else:
                # Should populate n_hat with layers that are controlled. Then go through n_hat.edges(data=True)
                # to find interdependencies.
                for t in range(T):
                    if t not in interdep_nodes:
                        interdep_nodes[t] = {}
                    if n_hat.has_node(v) and a['data']['inf_data'].is_interdep:
                        if functionality[t][u] == 0.0:
                            if v not in interdep_nodes[t]:
                                interdep_nodes[t][v] = []
                            interdep_nodes[t][v].append((u, a['data']['inf_data'].gamma))

        for t in range(T):
            # Add geographical space variables.
            if co_location:
                for s in S:
                    m.addVar(name='z_' + str(s.id) + "," + str(t), vtype=GRB.BINARY)
            # Add over/under-supply variables for each node.
            for n, d in n_hat.nodes(data=True):
                m.addVar(name='delta+_' + str(n) + "," + str(t), lb=0.0)
                m.addVar(name='delta-_' + str(n) + "," + str(t), lb=0.0)
                for layer in d['data']['inf_data'].extra_com.keys():
                    m.addVar(name='delta+_' + str(n) + "," + str(t) + "," + str(layer), lb=0.0)
                    m.addVar(name='delta-_' + str(n) + "," + str(t) + "," + str(layer), lb=0.0)
            # Add functionality binary variables for each node in N'.
            for n, d in n_hat.nodes(data=True):
                m.addVar(name='w_' + str(n) + "," + str(t), vtype=GRB.BINARY)
                if T > 1:
                    m.addVar(name='w_tilde_' + str(n) + "," + str(t), vtype=GRB.BINARY)
                    # Fix node values (only for iINDP)
            m.update()
            for key, val in fixed_nodes.items():
                m.getVarByName('w_' + str(key) + "," + str(0)).lb = val
                m.getVarByName('w_' + str(key) + "," + str(0)).ub = val
            # Add flow variables for each arc. (main commodity)
            for u, v, a in n_hat.edges(data=True):
                m.addVar(name='x_' + str(u) + "," + str(v) + "," + str(t), lb=0.0)
                for layer in a['data']['inf_data'].extra_com.keys():
                    m.addVar(name='x_' + str(u) + "," + str(v) + "," + str(t) + "," + str(layer), lb=0.0)
            # Add functionality binary variables for each arc in A'.
            for u, v, a in a_hat_prime:
                m.addVar(name='y_' + str(u) + "," + str(v) + "," + str(t), vtype=GRB.BINARY)
                if T > 1:
                    m.addVar(name='y_tilde_' + str(u) + "," + str(v) + "," + str(t), vtype=GRB.BINARY)
        m.update()

        # Populate objective function.
        obj_func = LinExpr()
        for t in range(T):
            if co_location:
                for s in S:
                    obj_func += s.cost * m.getVarByName('z_' + str(s.id) + "," + str(t))
            for u, v, a in a_hat_prime:
                if T == 1:
                    obj_func += (float(a['data']['inf_data'].reconstruction_cost) / 2.0) * m.getVarByName(
                        'y_' + str(u) + "," + str(v) + "," + str(t))
                else:
                    obj_func += (float(a['data']['inf_data'].reconstruction_cost) / 2.0) * m.getVarByName(
                        'y_tilde_' + str(u) + "," + str(v) + "," + str(t))
            for n, d in n_hat_prime:
                if T == 1:
                    obj_func += d['data']['inf_data'].reconstruction_cost * m.getVarByName('w_' + str(n) + "," + str(t))
                else:
                    obj_func += d['data']['inf_data'].reconstruction_cost * m.getVarByName(
                        'w_tilde_' + str(n) + "," + str(t))
            for n, d in n_hat.nodes(data=True):
                obj_func += d['data']['inf_data'].oversupply_penalty * m.getVarByName('delta+_' + str(n) + "," + str(t))
                obj_func += d['data']['inf_data'].undersupply_penalty * m.getVarByName(
                    'delta-_' + str(n) + "," + str(t))
                for layer, val in d['data']['inf_data'].extra_com.items():
                    obj_func += val['oversupply_penalty'] * m.getVarByName(
                        'delta+_' + str(n) + "," + str(t) + "," + str(layer))
                    obj_func += val['undersupply_penalty'] * m.getVarByName(
                        'delta-_' + str(n) + "," + str(t) + "," + str(layer))

            for u, v, a in n_hat.edges(data=True):
                obj_func += a['data']['inf_data'].flow_cost * m.getVarByName(
                    'x_' + str(u) + "," + str(v) + "," + str(t))
                for layer, val in a['data']['inf_data'].extra_com.items():
                    obj_func += val['flow_cost'] * m.getVarByName(
                        'x_' + str(u) + "," + str(v) + "," + str(t) + "," + str(layer))

        m.setObjective(obj_func, GRB.MINIMIZE)
        m.update()

        # Constraints.
        # Time-dependent constraints.
        if T > 1:
            for n, d in n_hat_prime:
                m.addConstr(m.getVarByName('w_' + str(n) + ",0"), GRB.EQUAL, 0,
                            "Initial state at node " + str(n) + "," + str(0))
            for u, v, a in a_hat_prime:
                m.addConstr(m.getVarByName('y_' + str(u) + "," + str(v) + ",0"), GRB.EQUAL, 0,
                            "Initial state at arc " + str(u) + "," + str(v) + "," + str(0))

        for t in range(T):
            # Time-dependent constraint.
            for n, d in n_hat_prime:
                if t > 0:
                    w_tilde_sum = LinExpr()
                    for t_prime in range(1, t + 1):
                        w_tilde_sum += m.getVarByName('w_tilde_' + str(n) + "," + str(t_prime))
                    m.addConstr(m.getVarByName('w_' + str(n) + "," + str(t)), GRB.LESS_EQUAL, w_tilde_sum,
                                "Time dependent recovery constraint at node " + str(n) + "," + str(t))
            for u, v, a in a_hat_prime:
                if t > 0:
                    y_tilde_sum = LinExpr()
                    for t_prime in range(1, t + 1):
                        y_tilde_sum += m.getVarByName('y_tilde_' + str(u) + "," + str(v) + "," + str(t_prime))
                    m.addConstr(m.getVarByName('y_' + str(u) + "," + str(v) + "," + str(t)), GRB.LESS_EQUAL,
                                y_tilde_sum,
                                "Time dependent recovery constraint at arc " + str(u) + "," + str(v) + "," + str(t))
            # Enforce a_i,j to be fixed if a_j,i is fixed (and vice versa).
            for u, v, a in a_hat_prime:
                # print u,",",v
                m.addConstr(m.getVarByName('y_' + str(u) + "," + str(v) + "," + str(t)), GRB.EQUAL,
                            m.getVarByName('y_' + str(v) + "," + str(u) + "," + str(t)),
                            "Arc reconstruction equality (" + str(u) + "," + str(v) + "," + str(t) + ")")
                if T > 1:
                    m.addConstr(m.getVarByName('y_tilde_' + str(u) + "," + str(v) + "," + str(t)), GRB.EQUAL,
                                m.getVarByName('y_tilde_' + str(v) + "," + str(u) + "," + str(t)),
                                "Arc reconstruction equality (" + str(u) + "," + str(v) + "," + str(t) + ")")
            # Conservation of flow constraint. (2) in INDP paper.
            for n, d in n_hat.nodes(data=True):
                out_flow_constr = LinExpr()
                in_flow_constr = LinExpr()
                demand_constr = LinExpr()
                for u, v, a in n_hat.out_edges(n, data=True):
                    out_flow_constr += m.getVarByName('x_' + str(u) + "," + str(v) + "," + str(t))
                for u, v, a in n_hat.in_edges(n, data=True):
                    in_flow_constr += m.getVarByName('x_' + str(u) + "," + str(v) + "," + str(t))
                demand_constr += d['data']['inf_data'].demand - m.getVarByName(
                    'delta+_' + str(n) + "," + str(t)) + m.getVarByName('delta-_' + str(n) + "," + str(t))
                m.addConstr(out_flow_constr - in_flow_constr, GRB.EQUAL, demand_constr,
                            "Flow conservation constraint " + str(n) + "," + str(t))
                for layer, val in d['data']['inf_data'].extra_com.items():
                    out_flow_constr = LinExpr()
                    in_flow_constr = LinExpr()
                    demand_constr = LinExpr()
                    for u, v, a in n_hat.out_edges(n, data=True):
                        out_flow_constr += m.getVarByName(
                            'x_' + str(u) + "," + str(v) + "," + str(t) + "," + str(layer))
                    for u, v, a in n_hat.in_edges(n, data=True):
                        in_flow_constr += m.getVarByName('x_' + str(u) + "," + str(v) + "," + str(t) + "," + str(layer))
                    demand_constr += val['demand'] - m.getVarByName(
                        'delta+_' + str(n) + "," + str(t) + "," + str(layer)) + m.getVarByName(
                        'delta-_' + str(n) + "," + str(t) + "," + str(layer))
                    m.addConstr(out_flow_constr - in_flow_constr, GRB.EQUAL, demand_constr,
                                "Flow conservation constraint " + str(n) + "," + str(t) + "," + str(layer))

            # Flow functionality constraints.
            if not functionality:
                interdep_nodes_list = interdep_nodes.keys()  # Interdependent nodes with a damaged dependee node
            else:
                interdep_nodes_list = interdep_nodes[t].keys()  # Interdependent nodes with a damaged dependee node
            for u, v, a in n_hat.edges(data=True):
                lhs = m.getVarByName('x_' + str(u) + "," + str(v) + "," + str(t)) + \
                      sum([m.getVarByName('x_' + str(u) + "," + str(v) + "," + str(t) + "," + str(layer)) for layer in
                           a['data']['inf_data'].extra_com.keys()])
                if (u in [n for (n, d) in n_hat_prime]) | (u in interdep_nodes_list):
                    m.addConstr(lhs, GRB.LESS_EQUAL,
                                a['data']['inf_data'].capacity * m.getVarByName('w_' + str(u) + "," + str(t)),
                                "Flow in functionality constraint(" + str(u) + "," + str(v) + "," + str(t) + ")")
                else:
                    m.addConstr(lhs, GRB.LESS_EQUAL,
                                a['data']['inf_data'].capacity * N.G.nodes[u]['data']['inf_data'].functionality,
                                "Flow in functionality constraint (" + str(u) + "," + str(v) + "," + str(t) + ")")
                if (v in [n for (n, d) in n_hat_prime]) | (v in interdep_nodes_list):
                    m.addConstr(lhs, GRB.LESS_EQUAL,
                                a['data']['inf_data'].capacity * m.getVarByName('w_' + str(v) + "," + str(t)),
                                "Flow out functionality constraint(" + str(u) + "," + str(v) + "," + str(t) + ")")
                else:
                    m.addConstr(lhs, GRB.LESS_EQUAL,
                                a['data']['inf_data'].capacity * N.G.nodes[v]['data']['inf_data'].functionality,
                                "Flow out functionality constraint (" + str(u) + "," + str(v) + "," + str(t) + ")")
                if (u, v, a) in a_hat_prime:
                    m.addConstr(lhs, GRB.LESS_EQUAL,
                                a['data']['inf_data'].capacity * m.getVarByName(
                                    'y_' + str(u) + "," + str(v) + "," + str(t)),
                                "Flow arc functionality constraint (" + str(u) + "," + str(v) + "," + str(t) + ")")
                else:
                    m.addConstr(lhs, GRB.LESS_EQUAL,
                                a['data']['inf_data'].capacity * N.G[u][v]['data']['inf_data'].functionality,
                                "Flow arc functionality constraint(" + str(u) + "," + str(v) + "," + str(t) + ")")

            # Resource availability constraints.
            for rc, val in v_r.items():
                is_sep_res = False
                if isinstance(val, int):
                    total_resource = val
                else:
                    is_sep_res = True
                    total_resource = sum([lval for _, lval in val.items()])
                    assert len(val.keys()) == len(layers), "The number of resource \
                        values does not match the number of layers."

                resource_left_constr = LinExpr()
                if is_sep_res:
                    res_left_constr_sep = {key: LinExpr() for key in val.keys()}

                for u, v, a in a_hat_prime:
                    idx_lyr = a['data']['inf_data'].layer
                    res_use = 0.5 * a['data']['inf_data'].resource_usage['h_' + rc]
                    if T == 1:
                        resource_left_constr += res_use * m.getVarByName('y_' + str(u) + "," + str(v) + "," + str(t))
                        if is_sep_res:
                            res_left_constr_sep[idx_lyr] += res_use * m.getVarByName(
                                'y_' + str(u) + "," + str(v) + "," + str(t))
                    else:
                        resource_left_constr += res_use * m.getVarByName(
                            'y_tilde_' + str(u) + "," + str(v) + "," + str(t))
                        if is_sep_res:
                            res_left_constr_sep[idx_lyr] += res_use * m.getVarByName(
                                'y_tilde_' + str(u) + "," + str(v) + "," + str(t))

                for n, d in n_hat_prime:
                    idx_lyr = n[1]
                    res_use = d['data']['inf_data'].resource_usage['p_' + rc]
                    if T == 1:
                        resource_left_constr += res_use * m.getVarByName('w_' + str(n) + "," + str(t))
                        if is_sep_res:
                            res_left_constr_sep[idx_lyr] += res_use * m.getVarByName('w_' + str(n) + "," + str(t))
                    else:
                        resource_left_constr += res_use * m.getVarByName('w_tilde_' + str(n) + "," + str(t))
                        if is_sep_res:
                            res_left_constr_sep[idx_lyr] += res_use * m.getVarByName('w_tilde_' + str(n) + "," + str(t))

                m.addConstr(resource_left_constr, GRB.LESS_EQUAL, total_resource, "Resource availability constraint "
                                                                                  "for " + rc + " at " + str(t) + ".")
                if is_sep_res:
                    for k, lval in val.items():
                        m.addConstr(res_left_constr_sep[k], GRB.LESS_EQUAL, lval, "Resource availability constraint "
                                                                                  "for " + rc + " at " + str(
                            t) + " for layer " + str(k) + ".")

            # Interdependency constraints
            infeasible_actions = []
            for n, d in n_hat.nodes(data=True):
                if not functionality:
                    if n in interdep_nodes:
                        interdep_l_constr = LinExpr()
                        interdep_r_constr = LinExpr()
                        for interdep in interdep_nodes[n]:
                            src = interdep[0]
                            gamma = interdep[1]
                            if not n_hat.has_node(src):
                                infeasible_actions.append(n)
                                interdep_l_constr += 0
                            else:
                                interdep_l_constr += m.getVarByName('w_' + str(src) + "," + str(t)) * gamma
                        interdep_r_constr += m.getVarByName('w_' + str(n) + "," + str(t))
                        m.addConstr(interdep_l_constr, GRB.GREATER_EQUAL, interdep_r_constr,
                                    "Interdependency constraint for node " + str(n) + "," + str(t))
                else:
                    if n in interdep_nodes[t]:
                        # print interdep_nodes[t]
                        interdep_l_constr = LinExpr()
                        interdep_r_constr = LinExpr()
                        for interdep in interdep_nodes[t][n]:
                            src = interdep[0]
                            gamma = interdep[1]
                            if not n_hat.has_node(src):
                                if print_cmd:
                                    print("Forcing", str(n), "to be 0 (dep. on", str(src), ")")
                                infeasible_actions.append(n)
                                interdep_l_constr += 0
                            else:
                                interdep_l_constr += m.getVarByName('w_' + str(src) + "," + str(t)) * gamma
                        interdep_r_constr += m.getVarByName('w_' + str(n) + "," + str(t))
                        m.addConstr(interdep_l_constr, GRB.GREATER_EQUAL, interdep_r_constr,
                                    "Interdependency constraint for node " + str(n) + "," + str(t))

            # Forced actions (if applicable)
            if forced_actions:
                recovery_sum = LinExpr()
                feasible_nodes = [(n, d) for n, d in n_hat_prime if n not in infeasible_actions]
                if len(feasible_nodes) + len(a_hat_prime) > 0:
                    for n, d in feasible_nodes:
                        if T == 1:
                            recovery_sum += m.getVarByName('w_' + str(n) + "," + str(t))
                        else:
                            recovery_sum += m.getVarByName('w_tilde_' + str(n) + "," + str(t))
                    for u, v, a in a_hat_prime:
                        if T == 1:
                            recovery_sum += m.getVarByName('y_' + str(u) + "," + str(v) + "," + str(t))
                        else:
                            recovery_sum += m.getVarByName('y_tilde_' + str(u) + "," + str(v) + "," + str(t))
                    m.addConstr(recovery_sum, GRB.GREATER_EQUAL, 1, "Forced action constraint")

            # Geographic space constraints
            if co_location:
                for s in S:
                    for n, d in n_hat_prime:
                        if d['data']['inf_data'].in_space(s.id):
                            if T == 1:
                                m.addConstr(
                                    m.getVarByName('w_' + str(n) + "," + str(t)) * d['data']['inf_data'].in_space(s.id),
                                    GRB.LESS_EQUAL, m.getVarByName('z_' + str(s.id) + "," + str(t)),
                                    "Geographical space constraint for node " + str(n) + "," + str(t))
                            else:
                                m.addConstr(
                                    m.getVarByName('w_tilde_' + str(n) + "," + str(t)) * d['data']['inf_data'].in_space(
                                        s.id), GRB.LESS_EQUAL, m.getVarByName('z_' + str(s.id) + "," + str(t)),
                                    "Geographical space constraint for node " + str(n) + "," + str(t))
                    for u, v, a in a_hat_prime:
                        if a['data']['inf_data'].in_space(s.id):
                            if T == 1:
                                m.addConstr(m.getVarByName('y_' + str(u) + "," + str(v) + "," + str(t)) * a['data'][
                                    'inf_data'].in_space(s.id), GRB.LESS_EQUAL,
                                            m.getVarByName('z_' + str(s.id) + "," + str(t)),
                                            "Geographical space constraint for arc (" + str(u) + "," + str(v) + ")")
                            else:
                                m.addConstr(
                                    m.getVarByName('y_tilde_' + str(u) + "," + str(v) + "," + str(t)) * a['data'][
                                        'inf_data'].in_space(s.id), GRB.LESS_EQUAL,
                                    m.getVarByName('z_' + str(s.id) + "," + str(t)),
                                    "Geographical space constraint for arc (" + str(u) + "," + str(v) + ")")
        m.update()
        # print("Solving... (%d vars)" % m.NumVars)
        if solution_pool:
            m.setParam('PoolSearchMode', 1)
            m.setParam('PoolSolutions', 10000)
            m.setParam('PoolGap', solution_pool)
        m.optimize()
        run_time = time.time() - start_time
        # Save results.
        if m.getAttr("Status") == GRB.OPTIMAL or m.status == 9:
            if m.status == 9:
                print('\nOptimizer time limit, gap = %1.3f\n' % m.MIPGap)
            results = INDPUtil.collect_results(m, controlled_layers, T, n_hat, n_hat_prime, a_hat_prime, S,
                                               coloc=co_location)
            results.add_run_time(t, run_time)
            if solution_pool:
                sol_pool_results = INDPUtil.collect_solution_pool(m, T, n_hat_prime, a_hat_prime)
                return [m, results, sol_pool_results]
            return [m, results]
        else:
            m.computeIIS()
            if m.status == 3:
                m.write("model.ilp")
                print(m.getAttr("Status"), ": SOLUTION NOT FOUND. (Check data and/or violated constraints).")
                print('\nThe following constraint(s) cannot be satisfied:')
                for c in m.getConstrs():
                    if c.IISConstr:
                        print('%s' % c.constrName)
            return None

    def get_spec(self):
        return {
            'name': 'INDP',
            'description': 'Interdependent Network Design Problem that models the restoration',
            'input_parameters': [
                {
                    'id': 'network_type',
                    'required': True,
                    'description': 'type of the network, which is set to `from_csv` for Seaside networks. '
                                   'e.g. from_csv, incore',
                    'type': str
                },
                {
                    'id': 'MAGS',
                    'required': True,
                    'description': 'sets the earthquake return period.',
                    'type': list
                },
                {
                    'id': 'sample_range',
                    'required': True,
                    'description': 'sets the range of sample scenarios to be analyzed',
                    'type': range
                },
                {
                    'id': 'dislocation_data_type',
                    'required': True,
                    'description': 'type of the dislocation data.',
                    'type': str
                },
                {
                    'id': 'return',
                    'required': True,
                    'description': 'type of the model for the return of the dislocated population. '
                                   'Options: *step_function* and *linear*.',
                    'type': str
                },
                {
                    'id': 'testbed_name',
                    'required': True,
                    'description': 'sets the name of the testbed in analysis',
                    'type': str
                },
                {
                    'id': 'extra_commodity',
                    'required': True,
                    'description': 'multi-commodity parameters dict',
                    'type': dict
                },
                {
                    'id': 'RC',
                    'required': True,
                    'description': 'list of resource caps or the number of available resources in each step of the '
                                   'analysis. Each item of the list is a dictionary whose items show the type of '
                                   'resource and the available number of that type of resource. For example: '
                                   '* If `FAIL_SCE_PARAM[TYPE]`=*from_csv*, you have two options:* if, for example, '
                                   '`R_c`= [{"budget": 3}, {"budget": 6}], then the analysis is done for the cases '
                                   'when there are 3 and 6 resources available of type "budget" '
                                   '(total resource assignment).* if, for example, `R_c`= [{"budget": {1:1, 2:1}}, '
                                   '{"budget": {1:1, 2:2}}, {"budget": {1:3, 2:3}}] and given there are 2 layers,'
                                   ' then the analysis is done for the case where each layer gets 1 resource of '
                                   'type "budget", AND the case where layer 1 gets 1 and layer 2 gets 2 resources of '
                                   'type "budget", AND the case where each layer gets 3 resources of type '
                                   '"budget" (Prescribed resource for each layer).',
                    'type': list
                },
                {
                    'id': 'layers',
                    'required': True,
                    'description': 'list of layers in the analysis',
                    'type': list
                },
                {
                    'id': 'method',
                    'required': True,
                    'description': 'There are two choices of method: 1. `INDP`: runs Interdependent Network '
                                   'Restoration Problem (INDP). 2. `TDINDP`: runs time-dependent INDP (td-INDP).  In '
                                   'both cases, if "TIME_RESOURCE" is True, then the repair time for each element '
                                   'is considered in devising the restoration plans',
                    'type': str,
                },
                {
                    'id': 't_steps',
                    'required': False,
                    'description': 'Number of time steps of the analysis',
                    'type': int
                },
                {
                    'id': 'time_resource',
                    'required': False,
                    'description': 'if TIME_RESOURCE is True, then the repair time for each element is '
                                   'considered in devising the restoration plans',
                    'type': bool
                }

            ],
            'input_datasets': [
                {
                    "id": "nodes_reptime_func",
                    "required": True,
                    "description": "repair time curves nodes",
                    "type": "incore:RepairTimeCurvesNodes"
                },
                {
                    "id": "nodes_damge_ratio",
                    "required": True,
                    "description": "damage ratio nodes",
                    "type": "incore:DamageRatioNodes"
                },
                {
                    "id": "arcs_reptime_func",
                    "required": True,
                    "description": "repair time curves arcs",
                    "type": "incore:RepairTimeCurvesArcs"
                },
                {
                    "id": "arcs_damge_ratio",
                    "required": True,
                    "description": "damage ratio arcs",
                    "type": "incore:DamageRatioArcs"
                },
                {
                    "id": "dmg_sce_data",
                    "required": True,
                    "description": "initial node ds",
                    "type": "incore:InitialNodeDS"
                },
                {
                    "id": "power_arcs",
                    "required": True,
                    "description": "Power Arcs",
                    "type": "incore:PowerArcs"
                },
                {
                    "id": "power_nodes",
                    "required": True,
                    "description": "Power Nodes",
                    "type": "incore:PowerNodes"
                },
                {
                    "id": "water_arcs",
                    "required": True,
                    "description": "Water Arcs",
                    "type": "incore:WaterArcs"
                },
                {
                    "id": "water_nodes",
                    "required": True,
                    "description": "Water Nodes",
                    "type": "incore:WaterNodes"
                },
                {
                    "id": "pipeline_dmg",
                    "required": True,
                    "description": "Pipeline Repair Rate output",
                    "type": "ergo:pipelineDamageVer3"
                },
                {
                    "id": "interdep",
                    "required": True,
                    "description": "Interdep.csv",
                    "type": "incore:Interdep"
                },
                {
                    "id": "initial_node",
                    "required": True,
                    "description": "initial node csv",
                    "type": "incore:InitialNode"
                },
                {
                    "id": "initial_link",
                    "required": True,
                    "description": "initial link csv",
                    "type": "incore:InitialLink"
                },
                {
                    "id": "pop_dislocation",
                    "required": True,
                    "description": "Population dislocation output",
                    "type": "incore:popDislocation"
                }
            ],
            'output_datasets': [

            ]
        }
