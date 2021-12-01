# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import BaseAnalysis


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

                # Check if the results exist
                out_dir_suffix_res = indp.get_resource_suffix(params)
                output_dir_full = params["OUTPUT_DIR"] + '_L' + str(len(params["L"])) + '_m' + \
                                  str(params["MAGNITUDE"]) + "_v" + out_dir_suffix_res + '/actions_' + str(i) + '_.csv'
                if os.path.exists(output_dir_full):
                    print('results are already there\n')
                    continue

                print('---Running Magnitude ' + str(m) + ' sample ' + str(i) + '...')
                if params['TIME_RESOURCE']:
                    print('Computing repair times...')
                    indp.time_resource_usage_curves(base_dir, damage_dir, i)

                print("Initializing network...")
                params["N"] = indp.initialize_network(base_dir=base_dir, extra_commodity=params["EXTRA_COMMODITY"])

                if params['DYNAMIC_PARAMS']:
                    print("Computing dynamic demand based on dislocation data...")
                    dyn_dmnd = dislocationutils.create_dynamic_param(params, N=params["N"], T=params["NUM_ITERATIONS"])
                    params['DYNAMIC_PARAMS']['DEMAND_DATA'] = dyn_dmnd

                if fail_sce_param['TYPE'] == 'from_csv':
                    indp.add_from_csv_failure_scenario(params["N"], sample=i, dam_dir=damage_dir)
                else:
                    sys.exit('Wrong failure scenario data type.')

                if params["ALGORITHM"] == "INDP":
                    indp.run_indp(params, layers=params['L'], controlled_layers=params['L'], T=params["T"],
                                  save_model=False, print_cmd_line=False, co_location=False)
                else:
                    sys.exit('Wrong algorithm type.')

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
