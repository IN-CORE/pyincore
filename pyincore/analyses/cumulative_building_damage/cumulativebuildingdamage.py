"""pyincore.analyses.bridgedamage.bridgedamage

Copyright (c) 2017 University of Illinois and others.  All rights reserved.
This program and the accompanying materials are made available under the
terms of the BSD-3-Clause which accompanies this distribution,
and is available at https://opensource.org/licenses/BSD-3-Clause

"""

import pandas as pd
import collections
import concurrent.futures
from itertools import repeat

from pyincore import BaseAnalysis, AnalysisUtil


class CumulativeBuildingDamage(BaseAnalysis):

    def run(self):
        """
        Executes Cumulative Building Damage Analysis
        """
        eq_damage_set = self.get_input_dataset("eq_bldg_dmg").get_csv_reader()
        eq_damage_df = pd.DataFrame(list(eq_damage_set))
        tsunami_damage_set = self.get_input_dataset("tsunami_bldg_dmg").get_csv_reader()
        tsunami_damage_df = pd.DataFrame(list(tsunami_damage_set))

        dmg_ratio_csv = self.get_input_dataset("dmg_ratios").get_csv_reader()
        dmg_ratio_tbl = AnalysisUtil.get_csv_table_rows(dmg_ratio_csv)

        user_defined_cpu = 1

        if not self.get_parameter("num_cpu") is None and self.get_parameter("num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self, len(eq_damage_df), user_defined_cpu)

        avg_bulk_input_size = int(len(eq_damage_df) / num_workers)
        eq_damage_args = []
        count = 0

        while count < len(eq_damage_df):
            eq_damage_args.append(eq_damage_df[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.cumulative_building_damage_concurrent_future(self.cumulative_building_damage_bulk_input,
                                                                    num_workers, eq_damage_args,
                                                                    repeat(tsunami_damage_df),
                                                                    repeat(dmg_ratio_tbl))

        self.set_result_csv_data("combined-result", results, name=self.get_parameter("result_name"))

        return True

    def cumulative_building_damage_concurrent_future(self, function_name, num_workers, *args):
        """
        Utilizes concurrent.future module
        :param function_name: the function to be parallelized
        :param num_workers: number of max workers in the parallelization
        :param args: all the arguments in order to pass into parameter function_namee
        :return: output: list of OrderedDict
        """

        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def cumulative_building_damage_bulk_input(self, eq_building_damage_set, tsunami_building_damage_set, dmg_ratio_tbl):
        """
        Runs analysis for multiple earthquake building damage results
        :param eq_building_damage_set: Multiple building damage results
        :param tsunami_building_damage_set: Set of all the tsunami building damage results
        :param dmg_ratio_tbl: damage ratios table
        :return: results: a list of Ordered Dict
        """

        result = []
        for idx, eq_building_damage in eq_building_damage_set.iterrows():
            result.append(self.cumulative_building_damage(eq_building_damage, tsunami_building_damage_set,
                                                          dmg_ratio_tbl))

        return result

    def cumulative_building_damage(self, eq_building_damage, tsunami_building_damage, dmg_ratio_tbl):
        guid = eq_building_damage['guid']

        tsunami_building = tsunami_building_damage.loc[tsunami_building_damage['guid'] == guid]

        for idy, tsunami_building in tsunami_building.iterrows():
            eq_limit_states = collections.OrderedDict()
            eq_limit_states['immocc'] = float(eq_building_damage["immocc"])
            eq_limit_states['lifesfty'] = float(eq_building_damage["lifesfty"])
            eq_limit_states['collprev'] = float(eq_building_damage["collprev"])

            tsunami_limit_states = collections.OrderedDict()
            tsunami_limit_states['immocc'] = float(tsunami_building["immocc"])
            tsunami_limit_states['lifesfty'] = float(tsunami_building["lifesfty"])
            tsunami_limit_states['collprev'] = float(tsunami_building["collprev"])

            limit_states = collections.OrderedDict()

            limit_states["collprev"] = eq_limit_states["collprev"] + tsunami_limit_states["collprev"] - \
                                       eq_limit_states["collprev"] * tsunami_limit_states["collprev"] + \
                                       ((eq_limit_states["lifesfty"] - eq_limit_states["collprev"]) *
                                        (tsunami_limit_states["lifesfty"] - tsunami_limit_states["collprev"]))

            limit_states["lifesfty"] = eq_limit_states["lifesfty"] + tsunami_limit_states["lifesfty"] - \
                                       eq_limit_states["lifesfty"] * tsunami_limit_states["lifesfty"] + \
                                       ((eq_limit_states["immocc"] - eq_limit_states["lifesfty"]) *
                                        (tsunami_limit_states["immocc"] - tsunami_limit_states["lifesfty"]))

            limit_states["immocc"] = eq_limit_states["immocc"] + tsunami_limit_states["immocc"] - \
                                     eq_limit_states["immocc"] * tsunami_limit_states["immocc"]

            damage_state = AnalysisUtil.calculate_damage_interval(limit_states)

            mean_damage = AnalysisUtil.calculate_mean_damage(dmg_ratio_tbl, damage_state)

            mean_damage_std_dev = AnalysisUtil.calculate_mean_damage_std_deviation(dmg_ratio_tbl,
                                                                                   damage_state,
                                                                                   mean_damage['meandamage'])
            bldg_results = collections.OrderedDict()

            bldg_results["guid"] = guid
            bldg_results["ls-immocc"] = limit_states["immocc"]
            bldg_results["ls-lifesfty"] = limit_states["lifesfty"]
            bldg_results["ls-collprev"] = limit_states["collprev"]
            bldg_results["ds-insignific"] = damage_state["insignific"]
            bldg_results["ds-moderate"] = damage_state["moderate"]
            bldg_results["ds-heavy"] = damage_state["heavy"]
            bldg_results["ds-complete"] = damage_state["complete"]
            bldg_results["meandamage"] = mean_damage["meandamage"]
            bldg_results["meandamage-dev"] = mean_damage_std_dev["mdamagedev"]
            bldg_results["hazard"] = "Earthquake+Tsunami"

            return bldg_results

    @staticmethod
    def load_csv_file(file_name):
        read_file = pd.read_csv(file_name, header="infer")
        return read_file

    def get_spec(self):
        return {
            'name': 'cumulative-building-damage',
            'description': 'cumulative building damage (earthquake + tsunami)',
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
                }
            ],
            'input_datasets': [
                {
                    'id': 'eq_bldg_dmg',
                    'required': True,
                    'description': 'Earthquake Building Damage Results',
                    'type': ['ergo:buildingDamageVer4'],
                },
                {
                    'id': 'tsunami_bldg_dmg',
                    'required': True,
                    'description': 'Tsunami Building Damage Results',
                    'type': ['ergo:buildingDamageVer4'],
                },
                {
                    'id': 'dmg_ratios',
                    'required': True,
                    'description': 'Mean Damage Ratios',
                    'type': ['ergo:buildingDamageRatios'],
                }
            ],
            'output_datasets': [
                {
                    'id': 'combined-result',
                    'parent_type': 'buildings',
                    'type': 'ergo:buildingDamageVer4'
                }

            ]
        }
