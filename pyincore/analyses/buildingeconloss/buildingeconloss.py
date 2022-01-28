# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd
import traceback

from pyincore import BaseAnalysis


class BuildingEconLoss(BaseAnalysis):
    """Direct Building Economic Loss analysis calculates the building loss based on
    building appraisal value, mean damage and an inflation multiplier from user's input.
    We are not implementing any inflation calculation based on consumer price indices
    at the moment. A user must supply the inflation percentage between a building appraisal
    year and year of interest (current, date of hazard etc.)

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        self.occ_damage_multipliers = None
        self.consumer_price_index = None
        # percentage
        self.infl_factor = 0.0

        super(BuildingEconLoss, self).__init__(incore_client)

    def run(self):
        """Executes building economic damage analysis."""

        # Get inflation input in %
        self.infl_factor = self.get_parameter("inflation_factor")

        # Building dataset
        bldg_set = self.get_input_dataset("buildings").get_inventory_reader()

        # Occupancy type of the exposure
        comp_type = self.get_parameter("component_type").lower()
        occ_mult_df = None
        if comp_type == "str" or comp_type == "as" or comp_type == "ds" or comp_type == "content":
            occ_multiplier = self.get_input_dataset("occupancy_multiplier").get_csv_reader()
            occ_mult_df = pd.DataFrame(occ_multiplier)
            for item in list(occ_multiplier):
                print(item)
            print(occ_mult_df)

        try:
            prop_select = []
            for bldg_item in list(bldg_set):
                guid = bldg_item["properties"]["guid"]
                appr_bldg = bldg_item["properties"]["appr_bldg"]
                year_built = bldg_item["properties"]["year_built"]
                occ_type = bldg_item["properties"]["occ_type"]
                prop_select.append([guid, year_built, occ_type, appr_bldg])

            bldg_set_df = pd.DataFrame(prop_select, columns=["guid", "year_built", "occ_type", "appr_bldg"])
            bldg_dmg_set = self.get_input_dataset("building_mean_dmg").get_csv_reader()
            bldg_dmg_df = pd.DataFrame(list(bldg_dmg_set))

            dmg_set_df = pd.merge(bldg_set_df, bldg_dmg_df, how="outer", left_on="guid", right_on="guid",
                                  sort=True, copy=True)
            infl_mult = self.get_inflation_mult()

            dmg_set_df = self.add_multiplies(dmg_set_df, occ_mult_df)

            bldg_results = dmg_set_df[["guid"]].copy()
            loss = 0.0
            lossdev = 0.0

            if "appr_bldg" in dmg_set_df:
                loss = dmg_set_df["appr_bldg"].astype(float) * dmg_set_df["meandamage"].astype(float) * infl_mult
                lossdev = dmg_set_df["appr_bldg"].astype(float) * dmg_set_df["mdamagedev"].astype(float) * infl_mult

            bldg_results["loss"] = loss.round(2)
            bldg_results["loss_dev"] = lossdev.round(2)

            result_name = self.get_parameter("result_name")
            if comp_type == "str":
                # structural damage
                result_name = result_name + "_str"
            elif comp_type == "as":
                # acceleration sensitive non-structural damage
                result_name = result_name + "_as"
            elif comp_type == "ds":
                # drift sensitive non-structural damage
                result_name = result_name + "_ds"
            elif comp_type == "content":
                # content damage
                result_name = result_name + "_cnt"

            self.set_result_csv_data("result", bldg_results, result_name, "dataframe")
            return True
        except Exception as e:
            # This prints the type, value and stacktrace of error being handled.
            traceback.print_exc()
            raise e

    def get_inflation_mult(self):
        """Get inflation multiplier from user's input.

        Returns:
            float: Inflation multiplier.

        """
        return (self.infl_factor / 100.0) + 1.0

    def add_multiplies(self, dmg_set_df, occ_mult_df):
        """Add occupancy multipliers to damage dataset.

        Args:
            dmg_set_df (pd.DataFrame): Building inventory dataset with guid and mean damages.
            occ_mult_df (pd.DataFrame): Occupation multiplier set.

        Returns:
            pd.DataFrame: Merged inventory.

        """
        if occ_mult_df is not None:
            occ_mult_df = occ_mult_df.rename(columns={"Multiplier": "occ_type"})
            dmg_set_df = pd.merge(dmg_set_df, occ_mult_df, how="left", left_on="occ_type", right_on="occ_type", sort=True, copy=True)
        else:
            dmg_set_df = dmg_set_df["occ_type"] = 1

        return dmg_set_df

    def get_spec(self):
        """Get specifications of the building damage analysis.

        Returns:
            obj: A JSON object of specifications of the building damage analysis.

        """
        return {
            'name': 'building-economy-damage',
            'description': 'building economy damage analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                },
                {
                    'id': 'component_type',
                    'required': False,
                    'description': 'Type of building component. This variable defines the structural and '
                                   'non-structural components of an inventory item (building) and the choice of '
                                   'corresponding occupancy multipliers. '
                                   'Values of the string are '
                                   'STR: structural, '
                                   'DS: drift-sensitive nonstructural, '
                                   'AS: acceleration-sensitive nonstructural, '
                                   'CONTENT: contents,'
                                   'default is STR',
                    'type': str
                },
                {
                    'id': 'inflation_factor',
                    'required': False,
                    'description': 'Inflation factor to adjust the appraisal values of buildings. Default 0.0',
                    'type': float
                },
            ],
            'input_datasets': [
                {
                    'id': 'buildings',
                    'required': True,
                    'description': 'Building Inventory',
                    'type': ['ergo:buildingInventory', 'ergo:buildingInventoryVer4',
                             'ergo:buildingInventoryVer5', 'ergo:buildingInventoryVer6',
                             'ergo:buildingInventoryVer7']
                },
                {
                    'id': 'building_mean_dmg',
                    'required': True,
                    'description': 'A CSV file with building mean damage results for either Structural, '
                                   'Drift-Sensitive Nonstructural, Acceleration-Sensitive Nonstructural '
                                   'or Contents Damage component.',
                    'type': ['ergo:meanDamage']
                },
                {
                    'id': 'occupancy_multiplier',
                    'required': False,
                    'description': 'Building occupancy damage multipliers. These multipliers account for the value '
                                   'associated with different types of components (structural, '
                                   'acceleration-sensitive nonstructural, '
                                   'drift-sensitive nonstructural, contents).',
                    'type': ['incore:buildingOccupancyMultiplier']
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'buildings',
                    'description': 'CSV file of building economy damages',
                    'type': 'incore:buildingEconomicLoss'
                }
            ]
        }
