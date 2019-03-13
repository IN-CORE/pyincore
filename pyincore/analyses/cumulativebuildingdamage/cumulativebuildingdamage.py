# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import pandas as pd
import collections
import concurrent.futures
from itertools import repeat

from pyincore import BaseAnalysis, AnalysisUtil


class CumulativeBuildingDamage(BaseAnalysis):
    """Cumulative building damage analysis."""
    def run(self):
        """Executes Cumulative Building Damage Analysis"""
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
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Maximum number workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with cumulative damage values and other data/metadata.

        """
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def cumulative_building_damage_bulk_input(self, eq_building_damage_set, tsunami_building_damage_set, dmg_ratio_tbl):
        """Run analysis for building damage results.

         Args:
             eq_building_damage_set (obj): A set of earthquake building damage results.
             tsunami_building_damage_set (obj): A set of all tsunami building damage results.
             dmg_ratio_tbl (obj): A damage ratio table, including weights to compute mean damage.

         Returns:
             list: A list of ordered dictionaries with multiple damage values and other data/metadata.
        """
        result = []
        for idx, eq_building_damage in eq_building_damage_set.iterrows():
            result.append(self.cumulative_building_damage(eq_building_damage, tsunami_building_damage_set,
                                                          dmg_ratio_tbl))

        return result

    def cumulative_building_damage(self, eq_building_damage, tsunami_building_damage, dmg_ratio_tbl):
        """Run analysis for building damage results.

         Args:
             eq_building_damage (obj): A JSON description of an earthquake building damage.
             tsunami_building_damage (obj): Set of all tsunami building damage results.
             dmg_ratio_tbl (obj): A damage ratio table, including weights to compute mean damage.

         Returns:
             OrderedDict: A dictionary with building damage values and other data/metadata.

        """
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

            limit_states["collprev"] = \
                eq_limit_states["collprev"] + tsunami_limit_states["collprev"] - \
                eq_limit_states["collprev"] * tsunami_limit_states["collprev"] + \
                ((eq_limit_states["lifesfty"] - eq_limit_states["collprev"]) *
                 (tsunami_limit_states["lifesfty"] - tsunami_limit_states["collprev"]))

            limit_states["lifesfty"] = \
                eq_limit_states["lifesfty"] + tsunami_limit_states["lifesfty"] - \
                eq_limit_states["lifesfty"] * tsunami_limit_states["lifesfty"] + \
                ((eq_limit_states["immocc"] - eq_limit_states["lifesfty"]) *
                 (tsunami_limit_states["immocc"] - tsunami_limit_states["lifesfty"]))

            limit_states["immocc"] = \
                eq_limit_states["immocc"] + tsunami_limit_states["immocc"] - \
                eq_limit_states["immocc"] * tsunami_limit_states["immocc"]

            damage_state = AnalysisUtil.calculate_damage_interval(limit_states)

            mean_damage = AnalysisUtil.calculate_mean_damage(dmg_ratio_tbl, damage_state)

            mean_damage_std_dev = \
                AnalysisUtil.calculate_mean_damage_std_deviation(dmg_ratio_tbl,
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
        """Load csv file into Pandas DataFrame.

        Args (str): Input csv file name.

        Returns:
            pd.DataFrame: A table from the csv with headers and values.

        """
        read_file = pd.read_csv(file_name, header="infer")
        return read_file

    def get_spec(self):
        """Get specifications of the damage analysis.

        Returns:
            obj: A JSON object of specifications of the cumulative damage analysis.

        """
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
                    'description': 'CSV file of building cumulative damage',
                    'type': 'ergo:buildingDamageVer4'
                }

            ]
        }
