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
        FAIL_SCE_PARAM = {
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

        DYNAMIC_PARAMS =
        EXTRA_COMMODITY =
        TIME_RESOURCE =

        runutils.run_method(FAIL_SCE_PARAM, RC, layers, method=method, t_steps=t_steps,
                            misc={'DYNAMIC_PARAMS': DYNAMIC_PARMAS, 'EXTRA_COMMODITY': EXTRA_COMMODITY,
                                  'TIME_RESOURCE':
                                True})

        runutils.run_method(FAIL_SCE_PARAM, RC, layers, method=method, t_steps=t_steps,
                            misc={'DYNAMIC_PARAMS': DYNAMIC_PARAMS, 'EXTRA_COMMODITY': EXTRA_COMMODITY,
                                  'TIME_RESOURCE': True})

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
                }

            ],
            'input_datasets': [

            ],
            'output_datasets': [

            ]
        }
