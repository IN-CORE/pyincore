# Copyright (c) 2022 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd
from pyincore import BaseAnalysis
from pyincore.utils.dataprocessutil import DataProcessUtil


class CombinedWindWaveSurgeBuildingDamage(BaseAnalysis):
    """Determines overall building maximum damage state from wind, flood and surge-wave damage
    and uses the maximum damage probabilities from the 3 damages to determine overall damage

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
        surge_wave_damage = self.get_input_dataset(
            "surge_wave_damage"
        ).get_dataframe_from_csv()

        # Read Building flood damage
        flood_damage = self.get_input_dataset("flood_damage").get_dataframe_from_csv()

        wind_max_damage = DataProcessUtil.get_max_damage_state(wind_damage)
        wind_max_damage.rename(
            columns={"max_state": "w_max_ds", "max_prob": "w_maxprob"}, inplace=True
        )

        surge_wave_max_damage = DataProcessUtil.get_max_damage_state(surge_wave_damage)
        surge_wave_max_damage.rename(
            columns={"max_state": "sw_max_ds", "max_prob": "sw_maxprob"}, inplace=True
        )

        flood_max_damage = DataProcessUtil.get_max_damage_state(flood_damage)
        flood_max_damage.rename(
            columns={"max_state": "f_max_ds", "max_prob": "f_maxprob"}, inplace=True
        )

        combined_output = pd.merge(
            pd.merge(wind_max_damage, surge_wave_max_damage, on="guid"),
            flood_max_damage,
            on="guid",
        )

        # Replace DS strings with integers to find maximum damage state
        replace_vals_int = {"DS_0": 0, "DS_1": 1, "DS_2": 2, "DS_3": 3}
        combined_output = combined_output.apply(
            lambda x: x.replace(replace_vals_int, regex=True)
        )

        # Find maximum among the max_ds columns
        max_damage_states = ["w_max_ds", "sw_max_ds", "f_max_ds"]
        max_val = combined_output[max_damage_states].max(axis=1)

        # Add maximum of the max damage states
        combined_output["max_state"] = max_val

        # Replace integers with DS strings
        old_ds_vals = [0, 1, 2, 3]
        new_ds_vals = ["DS_0", "DS_1", "DS_2", "DS_3"]

        # Put DS strings back in the final output before storing
        combined_output["w_max_ds"] = combined_output["w_max_ds"].replace(
            old_ds_vals, new_ds_vals
        )
        combined_output["sw_max_ds"] = combined_output["sw_max_ds"].replace(
            old_ds_vals, new_ds_vals
        )
        combined_output["f_max_ds"] = combined_output["f_max_ds"].replace(
            old_ds_vals, new_ds_vals
        )
        combined_output["max_state"] = combined_output["max_state"].replace(
            old_ds_vals, new_ds_vals
        )

        # Find combined damage
        combined_bldg_dmg = self.get_combined_damage(
            wind_damage, surge_wave_damage, flood_damage
        )

        # Create the result containing the 3 combined damages into a single damage
        self.set_result_csv_data(
            "ds_result",
            combined_bldg_dmg,
            self.get_parameter("result_name") + "_combined_dmg",
            "dataframe",
        )

        # Create the result dataset
        self.set_result_csv_data(
            "result",
            combined_output,
            self.get_parameter("result_name") + "_max_state",
            "dataframe",
        )

        return True

    def get_combined_damage(
        self, wind_dmg: pd.DataFrame, sw_dmg: pd.DataFrame, flood_dmg: pd.DataFrame
    ):
        """Calculates overall building damage
        Determines the overall building damage probabilities from the 3 hazards by taking the maximum.

        Args:
            wind_dmg (pd.DataFrame): Table of wind damage for the building inventory
            sw_dmg (pd.DataFrame): Table of surge-wave damage for the building inventory
            flood_dmg (pd.DataFrame): Table of flood damage for the building inventory

        Returns:
            pd.DataFrame: An table of combined damage probabilities for the building inventory

        """
        flood_dmg.rename(
            columns={
                "LS_0": "f_LS_0",
                "LS_1": "f_LS_1",
                "LS_2": "f_LS_2",
                "DS_0": "f_DS_0",
                "DS_1": "f_DS_1",
                "DS_2": "f_DS_2",
                "DS_3": "f_DS_3",
                "haz_expose": "f_haz_expose",
            },
            inplace=True,
        )

        sw_dmg.rename(
            columns={
                "LS_0": "sw_LS_0",
                "LS_1": "sw_LS_1",
                "LS_2": "sw_LS_2",
                "DS_0": "sw_DS_0",
                "DS_1": "sw_DS_1",
                "DS_2": "sw_DS_2",
                "DS_3": "sw_DS_3",
                "haz_expose": "sw_haz_expose",
            },
            inplace=True,
        )

        wind_dmg.rename(
            columns={
                "LS_0": "w_LS_0",
                "LS_1": "w_LS_1",
                "LS_2": "w_LS_2",
                "DS_0": "w_DS_0",
                "DS_1": "w_DS_1",
                "DS_2": "w_DS_2",
                "DS_3": "w_DS_3",
                "haz_expose": "w_haz_expose",
            },
            inplace=True,
        )

        combined_df = pd.merge(
            pd.merge(wind_dmg, sw_dmg, on="guid"), flood_dmg, on="guid"
        )

        def find_match(row, col_name):
            max_finder = {
                row["f_DS_3"]: "f_",
                row["w_DS_3"]: "w_",
                row["sw_DS_3"]: "sw_",
            }

            return row[max_finder[max(max_finder.keys())] + col_name]

        combined_df["LS_0"] = combined_df.apply(
            lambda x: find_match(x, col_name="LS_0"), axis=1
        )
        combined_df["LS_1"] = combined_df.apply(
            lambda x: find_match(x, col_name="LS_1"), axis=1
        )
        combined_df["LS_2"] = combined_df.apply(
            lambda x: find_match(x, col_name="LS_2"), axis=1
        )
        combined_df["DS_0"] = combined_df.apply(
            lambda x: find_match(x, col_name="DS_0"), axis=1
        )
        combined_df["DS_1"] = combined_df.apply(
            lambda x: find_match(x, col_name="DS_1"), axis=1
        )
        combined_df["DS_2"] = combined_df.apply(
            lambda x: find_match(x, col_name="DS_2"), axis=1
        )
        combined_df["DS_3"] = combined_df.apply(
            lambda x: find_match(x, col_name="DS_3"), axis=1
        )
        combined_df["haz_expose"] = combined_df.apply(
            lambda x: find_match(x, col_name="haz_expose"), axis=1
        )

        # Remove extra columns that are no longer needed
        combined_df.drop(
            [
                "w_LS_0",
                "w_LS_1",
                "w_LS_2",
                "sw_LS_0",
                "sw_LS_1",
                "sw_LS_2",
                "f_LS_0",
                "f_LS_1",
                "f_LS_2",
                "w_DS_0",
                "w_DS_1",
                "w_DS_2",
                "w_DS_3",
                "sw_DS_0",
                "sw_DS_1",
                "sw_DS_2",
                "sw_DS_3",
                "f_DS_0",
                "f_DS_1",
                "f_DS_2",
                "f_DS_3",
                "w_haz_expose",
                "sw_haz_expose",
                "f_haz_expose",
            ],
            axis=1,
            inplace=True,
        )

        return combined_df

    def get_spec(self):
        """Get specifications of the combined wind, wave, and surge building damage analysis.

        Returns:
            obj: A JSON object of specifications of the combined wind, wave, and surge building damage analysis.

        """
        return {
            "name": "combined-wind-wave-surge-building-damage",
            "description": "Combined wind wave and surge building damage analysis",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "result dataset name",
                    "type": str,
                },
            ],
            "input_datasets": [
                {
                    "id": "wind_damage",
                    "required": True,
                    "description": "Wind damage result that has damage intervals in it",
                    "type": ["ergo:buildingDamageVer6"],
                },
                {
                    "id": "surge_wave_damage",
                    "required": True,
                    "description": "Surge-wave damage result that has damage intervals in it",
                    "type": ["ergo:buildingDamageVer6"],
                },
                {
                    "id": "flood_damage",
                    "required": True,
                    "description": "Flood damage result that has damage intervals in it",
                    "type": ["ergo:nsBuildingInventoryDamageVer4"],
                },
            ],
            "output_datasets": [
                {
                    "id": "ds_result",
                    "parent_type": "buildings",
                    "description": "CSV file of damage states for building structural damage",
                    "type": "ergo:buildingDamageVer6",
                },
                {
                    "id": "result",
                    "parent_type": "buildings",
                    "description": "CSV file of building maximum damage state",
                    "type": "incore:maxDamageState",
                },
            ],
        }
