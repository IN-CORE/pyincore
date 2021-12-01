# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import BaseAnalysis
from pyincore.analyses.indp import INDPUtil
from pyincore.analyses.indp.infrastructure import add_from_csv_failure_scenario
from pyincore.analyses.indp.dislocationutils import DislocationUtil


class INDP(BaseAnalysis):

    def __init__(self, incore_client):
        super(INDP, self).__init__(incore_client)

    def run(self):

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
            is run given the total number of resources. If this is a list of lists of floats, each list is interpreted as
            fixed upper bounds on the number of resources each layer can use (same for all time steps).
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

        # Set root directories
        base_dir = fail_sce_param['BASE_DIR']
        damage_dir = fail_sce_param['DAMAGE_DIR']

        print('----Running for resources: ' + str(params['V']))
        for m in fail_sce_param['MAGS']:
            for i in fail_sce_param['SAMPLE_RANGE']:
                params["SIM_NUMBER"] = i
                params["MAGNITUDE"] = m

                print('---Running Magnitude ' + str(m) + ' sample ' + str(i) + '...')
                if params['TIME_RESOURCE']:
                    print('Computing repair times...')
                    INDPUtil.time_resource_usage_curves(base_dir, damage_dir, i)

                print("Initializing network...")
                params["N"] = INDPUtil.initialize_network(base_dir=base_dir, extra_commodity=params["EXTRA_COMMODITY"])

                if params['DYNAMIC_PARAMS']:
                    print("Computing dynamic demand based on dislocation data...")
                    dyn_dmnd = DislocationUtil.create_dynamic_param(params, N=params["N"], T=params["NUM_ITERATIONS"])
                    params['DYNAMIC_PARAMS']['DEMAND_DATA'] = dyn_dmnd

                if fail_sce_param['TYPE'] == 'from_csv':
                    add_from_csv_failure_scenario(params["N"], sample=i, dam_dir=damage_dir)
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
            controlled_layers (list): List of layers that are included in the analysis. The default is 'None', which sets the list equal to layers.
            functionality (dict): This dictionary is used to assign functionality values elements in the network before the analysis starts. The
            default is 'None'.
            T (int): Number of time steps to optimize over. T=1 shows an iINDP analysis, and T>1 shows a td-INDP. The default is 1.
            TODO save & suffice aare not exposed to outside should remove it
            save (bool): If the results should be saved to file. The default is True.
            suffix (str): The suffix that should be added to the output files when saved. The default is ''.

            forced_actions (bool): If True, the optimizer is forced to repair at least one element in each time step. The default is False.
            TODO expose this parameter
            save_model (bool): If the Gurobi optimization model should be saved to file. The default is False.
            TODO expose this parameter
            print_cmd_line (bool): If full information about the analysis should be written to the console. The default is True.
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

        if "N" not in params:
            interdependent_net = INDPUtil.initialize_network(base_dir="../data/INDP_7-20-2015/", sim_number=params[
                'SIM_NUMBER'], magnitude=params["MAGNITUDE"])
        else:
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
            output_dir = params["OUTPUT_DIR"] + '_L' + str(len(layers)) + '_m' + str(params["MAGNITUDE"]) + \
                         "_v" + out_dir_suffix_res
            # Initial calculations.
            if params['DYNAMIC_PARAMS']:
                original_N = copy.deepcopy(interdependent_net)  # !!! deepcopy
                dislocationutils.dynamic_parameters(interdependent_net, original_N, 0,
                                                    params['DYNAMIC_PARAMS']['DEMAND_DATA'])
            v_0 = {x: 0 for x in params["V"].keys()}
            results = indp(interdependent_net, v_0, 1, layers, controlled_layers=controlled_layers,
                           functionality=functionality, co_location=co_location)
            indp_results = results[1]
            indp_results.add_components(0, INDPComponents.calculate_components(results[0], interdependent_net,
                                                                               layers=controlled_layers))
            for i in range(params["NUM_ITERATIONS"]):
                print("-Time Step (iINDP)", i + 1, "/", params["NUM_ITERATIONS"])
                if params['DYNAMIC_PARAMS']:
                    dislocationutils.dynamic_parameters(interdependent_net, original_N, i + 1,
                                                        params['DYNAMIC_PARAMS']['DEMAND_DATA'])
                results = indp(interdependent_net, params["V"], T, layers, controlled_layers=controlled_layers,
                               forced_actions=forced_actions, co_location=co_location)
                indp_results.extend(results[1], t_offset=i + 1)
                if save_model:
                    save_indp_model_to_file(results[0], output_dir + "/Model", i + 1)
                # Modify network to account for recovery and calculate components.
                apply_recovery(interdependent_net, indp_results, i + 1)
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
            results = indp(interdependent_net, v_0, 1, layers, controlled_layers=controlled_layers,
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
                results = indp(interdependent_net, params["V"], time_window_length + 1, layers,
                               controlled_layers=controlled_layers, functionality=functionality_t,
                               forced_actions=forced_actions, co_location=co_location)
                if save_model:
                    save_indp_model_to_file(results[0], output_dir + "/Model", n + 1)
                if "WINDOW_LENGTH" in params:
                    indp_results.extend(results[1], t_offset=n + 1, t_start=1, t_end=2)
                    # Modify network for recovery actions and calculate components.
                    apply_recovery(interdependent_net, results[1], 1)
                    indp_results.add_components(n + 1,
                                                INDPComponents.calculate_components(results[0], interdependent_net,
                                                                                    1, layers=controlled_layers))
                else:
                    indp_results.extend(results[1], t_offset=0)
                    for t in range(1, T):
                        # Modify network to account for recovery actions.
                        apply_recovery(interdependent_net, indp_results, t)
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

            ],
            'output_datasets': [

            ]
        }
