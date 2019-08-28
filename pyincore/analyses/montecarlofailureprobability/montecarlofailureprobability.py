# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import collections
import concurrent.futures

from pyincore import BaseAnalysis, AnalysisUtil
import random


class MonteCarloFailureProbability(BaseAnalysis):
    """
    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(MonteCarloFailureProbability, self).__init__(incore_client)

    def get_spec(self):
        """Get specifications of the monte carlo failure probability analysis.

        Returns:
            obj: A JSON object of specifications of the monte carlo failure probability analysis.

        """
        return {
            'name': 'monte-carlo-failure-probability',
            'description': 'calculate the probability of failure in monte-carlo simulation',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                },
                {
                    'id': 'num_cpu',
                    'required': False,
                    'description': 'If using parallel execution, the number of cpus to request',
                    'type': int
                },
                {
                    'id': 'num_samples',
                    'required': True,
                    'description': 'Number of MC samples',
                    'type': int
                },
                {
                    'id': 'damage_interval_keys',
                    'required': True,
                    'description': 'Column name of the damage interval',
                    'type': list
                },
                {
                    'id': 'failure_state_keys',
                    'required': True,
                    'description': 'Column name of the damage interval that considered as damaged',
                    'type': list
                }
            ],
            'input_datasets': [
                {
                    'id': 'damage',
                    'required': True,
                    'description': 'damage result that has damage intervals in it',
                    'type': ['ergo:buildingDamageVer4', 'bridge-damage',
                             'ergo:waterFacilityDamageVer4'],
                },

            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'description': 'CSV file of failure probability',
                    'type': 'incore:failureProbability'
                }
            ]
        }

    def run(self):
        """Executes mc failure probability analysis."""

        # read in file and parameters
        damage = self.get_input_dataset("damage").get_csv_reader()
        damage_result = AnalysisUtil.get_csv_table_rows(damage, ignore_first_row=False)

        # setting number of cpus to use
        user_defined_cpu = 1
        if not self.get_parameter("num_cpu") is None and self.get_parameter(
                "num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self,
                                                                 len(
                                                                     damage_result),
                                                                 user_defined_cpu)

        avg_bulk_input_size = int(len(damage_result) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = damage_result
        while count < len(inventory_list):
            inventory_args.append(
                inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.monte_carlo_failure_probability_concurrent_future(
            self.monte_carlo_failure_probability_bulk_input, num_workers,
            inventory_args)
        self.set_result_csv_data("result", results,
                                 name=self.get_parameter("result_name"))
        return True

    def monte_carlo_failure_probability_concurrent_future(self, function_name,
                                                          parallelism, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            parallelism (int): Number of workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        output = []
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=parallelism) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def monte_carlo_failure_probability_bulk_input(self, damage):
        """Run analysis for monte carlo failure probability calculation

        Args:
            damage (obj): output of building/bridge/waterfacility/epn damage that has damage interval

        Returns:
            list: A list of ordered dictionaries with probability failure and other data/metadata.

        """
        damage_interval_keys = self.get_parameter("damage_interval_keys")
        failure_state_keys = self.get_parameter("failure_state_keys")
        num_samples = self.get_parameter("num_samples")

        result = []
        for dmg in damage:
            result.append(
                self.monte_carlo_failure_probability(dmg,
                                                     damage_interval_keys,
                                                     failure_state_keys,
                                                     num_samples))

        return result

    def monte_carlo_failure_probability(self, dmg, damage_interval_keys,
                                        failure_state_keys, num_samples):
        """Calculates building damage results for a single building.

        Args:
            dmg (obj): dmg analysis output for a single entry.
            damage_interval_keys (list): list of the name of the damage intervals
            failure_state_keys (list): list of the name of the damage state that is considered as failed
            num_samples: number of samples for mc simulation

        Returns:
            OrderedDict: A dictionary with failure probability and other data/metadata.

        """
        fp_results = collections.OrderedDict()
        fp_results.update(dmg)

        ds_sample = self.sample_damage_interval(dmg, damage_interval_keys,
                                                num_samples)
        fp_results[
            'failure_probability'] = self.calc_probability_failure_value(
            ds_sample, failure_state_keys)

        return fp_results

    def sample_damage_interval(self, dmg, damage_interval_keys, num_samples):
        """
        Dylan Sanderson code to calculate the monte carlo simulations of damage state
        Args:
            dmg: damage results that contains dmg interval values
            damage_interval_keys: keys of the damage states
            num_samples: number of simulation

        Returns: dictionary of {sample_n: dmg_state}

        """
        ds = {}
        for i in range(num_samples):
            rnd_num = random.uniform(0, 1)
            prob_val = 0
            for ds_name in damage_interval_keys:
                if rnd_num < prob_val + float(dmg[ds_name]):
                    ds['sample_{}'.format(i)] = ds_name
                    break
                else:
                    prob_val += float(dmg[ds_name])
        return ds

    def calc_probability_failure_value(self, ds_sample, failure_state_keys):
        """
        Lisa Wang's approach to calculate a single value of failure probability
        Args:
            ds_sample: dictionary of { sample_n: dmg_state }
            failure_state_keys: damage state keys that considered as failure
            num_samples: num of samples

        Returns: failure probability (0 - 1)

        """
        count = 0
        for key in ds_sample.values():
            if key in failure_state_keys:
                count += 1

        return count / len(ds_sample)