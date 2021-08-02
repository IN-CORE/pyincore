# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import collections
import concurrent.futures
import numpy as np

from pyincore import BaseAnalysis, AnalysisUtil


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
                    'description': 'basename of the result datasets. This analysis will create two outputs: failure '
                                   'proability and failure state with the basename in the filename. '
                                   'For example: "result_name = joplin_mcs_building" will result in '
                                   '"joplin_mcs_building_failure_state.csv" and '
                                   '"joplin_mcs_building_failure_probability.csv"',
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
                },
                {
                    'id': 'seed',
                    'required': False,
                    'description': 'Initial seed for the probabilistic model',
                    'type': int
                },
            ],
            'input_datasets': [
                {
                    'id': 'damage',
                    'required': True,
                    'description': 'damage result that has damage intervals in it',
                    'type': ['ergo:buildingDamageVer4',
                             'ergo:buildingDamageVer5',
                             'ergo:buildingDamageVer6',
                             'ergo:nsBuildingInventoryDamage',
                             'ergo:nsBuildingInventoryDamageVer2',
                             'ergo:nsBuildingInventoryDamageVer3',
                             'ergo:bridgeDamage',
                             'ergo:bridgeDamageVer2',
                             'ergo:bridgeDamageVer3',
                             'ergo:waterFacilityDamageVer4',
                             'ergo:waterFacilityDamageVer5',
                             'ergo:waterFacilityDamageVer6',
                             'ergo:roadDamage',
                             'ergo:roadDamageVer2',
                             'ergo:roadDamageVer3',
                             'incore:epfDamage',
                             'incore:epfDamageVer2',
                             'incore:epfDamageVer3',
                             'incore:pipelineDamage',
                             'incore:pipelineDamageVer2',
                             'incore:pipelineDamageVer3']
                },

            ],
            'output_datasets': [
                {
                    'id': 'failure_probability',
                    'description': 'CSV file of failure probability',
                    'type': 'incore:failureProbability'
                },
                {
                    'id': 'sample_failure_state',
                    'description': 'CSV file of failure state for each sample',
                    'type': 'incore:sampleFailureState'
                },
                {
                    'id': 'sample_damage_states',
                    'description': 'CSV file of simulated damage states for each sample',
                    'type': 'incore:sampleDamageState'
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

        seed = self.get_parameter("seed")
        seed_list = []
        if seed is not None:
            while count < len(inventory_list):
                inventory_args.append(
                    inventory_list[count:count + avg_bulk_input_size])
                seed_list.append([seed + i for i in range(count - 1, count + avg_bulk_input_size - 1)])
                count += avg_bulk_input_size
        else:
            while count < len(inventory_list):
                inventory_args.append(
                    inventory_list[count:count + avg_bulk_input_size])
                seed_list.append([None for i in range(count - 1, count + avg_bulk_input_size - 1)])
                count += avg_bulk_input_size

        fs_results, fp_results, samples_results = self.monte_carlo_failure_probability_concurrent_future(
            self.monte_carlo_failure_probability_bulk_input, num_workers,
            inventory_args, seed_list)
        self.set_result_csv_data("sample_failure_state",
                                 fs_results, name=self.get_parameter("result_name") + "_failure_state")
        self.set_result_csv_data("failure_probability",
                                 fp_results, name=self.get_parameter("result_name") + "_failure_probability")
        self.set_result_csv_data("sample_damage_states",
                                 samples_results, name=self.get_parameter("result_name") + "_sample_damage_states")
        return True

    def monte_carlo_failure_probability_concurrent_future(self, function_name,
                                                          parallelism, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            parallelism (int): Number of workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of dictionary with id/guid and failure state for N samples.
            list: A list dictionary with failure probability and other data/metadata.

        """
        fs_output = []
        fp_output = []
        samples_output = []
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=parallelism) as executor:
            for fs_ret, fp_ret, samples_ret in executor.map(function_name, *args):
                fs_output.extend(fs_ret)
                fp_output.extend(fp_ret)
                samples_output.extend(samples_ret)

        return fs_output, fp_output, samples_output

    def monte_carlo_failure_probability_bulk_input(self, damage, seed_list):
        """Run analysis for monte carlo failure probability calculation

        Args:
            damage (obj): An output of building/bridge/waterfacility/epn damage that has damage interval.
            seed_list (list): Random number generator seed per building for reproducibility.

        Returns:
            fs_results (list): A list of dictionary with id/guid and failure state for N samples
            fp_results (list): A list dictionary with failure probability and other data/metadata.

        """
        damage_interval_keys = self.get_parameter("damage_interval_keys")
        failure_state_keys = self.get_parameter("failure_state_keys")
        num_samples = self.get_parameter("num_samples")

        fs_result = []
        fp_result = []
        samples_output = []

        i = 0
        for dmg in damage:
            fs, fp, samples_result = self.monte_carlo_failure_probability(dmg, damage_interval_keys, failure_state_keys,
                                                                          num_samples, seed_list[i])
            fs_result.append(fs)
            fp_result.append(fp)
            samples_output.append(samples_result)
            i += 1

        return fs_result, fp_result, samples_output

    def monte_carlo_failure_probability(self, dmg, damage_interval_keys,
                                        failure_state_keys, num_samples, seed):
        """Calculates building damage results for a single building.

        Args:
            dmg (obj): Damage analysis output for a single entry.
            damage_interval_keys (list): A list of the name of the damage intervals.
            failure_state_keys (list): A list of the name of the damage state that is considered as failed.
            num_samples (int): Number of samples for mc simulation.
            seed (int): Random number generator seed for reproducibility.

        Returns:
            dict: A dictionary with id/guid and failure state for N samples
            dict: A dictionary with failure probability and other data/metadata.
            dict: A dictionary with id/guid and damage states for N samples

        """
        # failure state
        fs_result = collections.OrderedDict()

        # sample damage states
        samples_result = collections.OrderedDict()

        # copying guid/id column to the sample damage failure table
        if 'guid' in dmg.keys():
            fs_result['guid'] = dmg['guid']
            samples_result['guid'] = dmg['guid']

        elif 'id' in dmg.keys():
            fs_result['id'] = dmg['id']
            samples_result['id'] = dmg['id']
        else:
            fs_result['id'] = 'NA'
            samples_result['id'] = 'NA'

        # failure probability
        fp_result = collections.OrderedDict()
        fp_result.update(dmg)

        ds_sample = self.sample_damage_interval(dmg, damage_interval_keys,
                                                num_samples, seed)
        func, fp = self.calc_probability_failure_value(ds_sample, failure_state_keys)

        fs_result['failure'] = ",".join(func.values())
        fp_result['failure_probability'] = fp
        samples_result['sample_damage_states'] = ','.join(ds_sample.values())

        return fs_result, fp_result, samples_result

    def sample_damage_interval(self, dmg, damage_interval_keys, num_samples, seed):
        """
        Dylan Sanderson code to calculate the Monte Carlo simulations of damage state.

        Args:
            dmg (dict): Damage results that contains dmg interval values.
            damage_interval_keys (list): Keys of the damage states.
            num_samples (int): Number of simulation.
            seed (int): Random number generator seed for reproducibility.

        Returns:
            dict: A dictionary of damage states.

        """
        ds = {}
        random_generator = np.random.RandomState(seed)
        for i in range(num_samples):
            # each sample should have a unique seed
            rnd_num = random_generator.uniform(0, 1)
            prob_val = 0
            flag = True
            for ds_name in damage_interval_keys:

                if rnd_num < prob_val + AnalysisUtil.float_to_decimal(dmg[ds_name]):
                    ds['sample_{}'.format(i)] = ds_name
                    flag = False
                    break
                else:
                    prob_val += AnalysisUtil.float_to_decimal(dmg[ds_name])
            if flag:
                print("cannot determine MC damage state!")

        return ds

    def calc_probability_failure_value(self, ds_sample, failure_state_keys):
        """
        Lisa Wang's approach to calculate a single value of failure probability.

        Args:
            ds_sample (dict): A dictionary of damage states.
            failure_state_keys (list): Damage state keys that considered as failure.

        Returns:
            float: Failure state on each sample 0 (failed), 1 (not failed).
            float: Failure probability (0 - 1).

        """
        count = 0
        func = {}
        for sample, state in ds_sample.items():
            if state in failure_state_keys:
                func[sample] = "0"
                count += 1
            else:
                func[sample] = "1"

        return func, count / len(ds_sample)
