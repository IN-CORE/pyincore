# Copyright (c) 2022 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd
from pyincore import BaseAnalysis
from pyincore.utils.dataprocessutil import DataProcessUtil


class CombinedWindWaveSurgeBuildingDamage(BaseAnalysis):
    """ Determines overall building maximum damage state from wind, flood and surge-wave damage
    
    Args:
        incore_client (IncoreClient): Service authentication.
    """

    def __init__(self, incore_client):
        super(CombinedWindWaveSurgeBuildingDamage, self).__init__(incore_client)

    def run(self):
        """Executes combined wind, wave, surge building damage analysis."""
        # Read Building wind damage
        wind_damage = self.get_input_dataset("wind_damage").get_dataframe_from_csv()

        # Read Building surge-wave damage
        surge_wave_damage = self.get_input_dataset("surge_wave_damage").get_dataframe_from_csv()

        # Read Building flood damage
        flood_damage = self.get_input_dataset("flood_damage").get_dataframe_from_csv()

        wind_max_damage = DataProcessUtil.get_max_damage_state(wind_damage)
        wind_max_damage.rename(columns={'max_state': 'w_max_ds', 'max_prob': 'w_maxprob'}, inplace=True)

        surge_wave_max_damage = DataProcessUtil.get_max_damage_state(surge_wave_damage)
        surge_wave_max_damage.rename(columns={'max_state': 'sw_max_ds', 'max_prob': 'sw_maxprob'}, inplace=True)

        flood_max_damage = DataProcessUtil.get_max_damage_state(flood_damage)
        flood_max_damage.rename(columns={'max_state': 'f_max_ds', 'max_prob': 'f_maxprob'}, inplace=True)

        combined_output = pd.merge(pd.merge(wind_max_damage, surge_wave_max_damage, on='guid'), flood_max_damage,
                                   on='guid')
        
        # Replace DS strings with integers to find maximum damage state
        replace_vals_int = {'DS_0': 0, 'DS_1': 1, 'DS_2': 2, 'DS_3': 3}
        combined_output = combined_output.apply(lambda x: x.replace(replace_vals_int, regex=True))

        # Find maximum among the max_ds columns
        max_damage_states = {'w_max_ds', 'sw_max_ds', 'f_max_ds'}
        max_val = combined_output[max_damage_states].max(axis=1)

        # Add maximum of the max damage states
        combined_output['max_state'] = max_val

        # Replace integers with DS strings
        old_ds_vals = [0, 1, 2, 3]
        new_ds_vals = ['DS_0', 'DS_1', 'DS_2', 'DS_3']

        # Put DS strings back in the final output before storing
        combined_output['w_max_ds'] = combined_output['w_max_ds'].replace(old_ds_vals, new_ds_vals)
        combined_output['sw_max_ds'] = combined_output['sw_max_ds'].replace(old_ds_vals, new_ds_vals)
        combined_output['f_max_ds'] = combined_output['f_max_ds'].replace(old_ds_vals, new_ds_vals)
        combined_output['max_state'] = combined_output['max_state'].replace(old_ds_vals, new_ds_vals)

        # Create the result dataset
        self.set_result_csv_data("result", combined_output, self.get_parameter("result_name"), "dataframe")

        return True

    def get_spec(self):
        """Get specifications of the combined wind, wave, and surge building damage analysis.

        Returns:
            obj: A JSON object of specifications of the combined wind, wave, and surge building damage analysis.

        """
        return {
            'name': 'combined-wind-wave-surge-building-damage',
            'description': 'Combined wind wave and surge building damage analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                },
            ],
            'input_datasets': [
                {
                    'id': 'wind_damage',
                    'required': True,
                    'description': 'Wind damage result that has damage intervals in it',
                    'type': ['ergo:buildingDamageVer6']
                },
                {
                    'id': 'surge_wave_damage',
                    'required': True,
                    'description': 'Surge-wave damage result that has damage intervals in it',
                    'type': ['ergo:buildingDamageVer6']
                },
                {
                    'id': 'flood_damage',
                    'required': True,
                    'description': 'Flood damage result that has damage intervals in it',
                    'type': ['ergo:buildingDamageVer6']
                },

            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'buildings',
                    'description': 'CSV file of building maximum damage state',
                    'type': 'incore:maxDamageState'
                }
            ]
        }
