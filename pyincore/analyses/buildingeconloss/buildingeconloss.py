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

        # Building occupancy multipliers for non structural and other losses
        occ_dmg_multiplier = self.get_input_dataset("building_occupancy").get_inventory_reader()
        if occ_dmg_multiplier is not None:
            occ_dmg_multiplier = occ_dmg_multiplier.get_dataframe_from_csv(low_memory=False)
        else:
            occ_dmg_multiplier = None

        try:
            prop_select = []
            for bldg_item in list(bldg_set):
                guid = bldg_item["properties"]["guid"]
                appr_bldg = bldg_item["properties"]["appr_bldg"]
                prop_select.append([guid, appr_bldg])

            bldg_set_df = pd.DataFrame(prop_select, columns=["guid", "appr_bldg"])
            bldg_dmg_set = self.get_input_dataset("building_mean_dmg").get_csv_reader()
            bldg_dmg_df = pd.DataFrame(list(bldg_dmg_set))

            dmg_set_df = pd.merge(bldg_set_df, bldg_dmg_df, how="outer", left_on="guid", right_on="guid",
                                  sort=True, copy=True)
            infl_mult = self.get_inflation_mult()

            bldg_results = dmg_set_df[["guid"]].copy()
            valloss = 0.0
            vallossdev = 0.0

            accloss = 0.0
            accloss = 0.0
            driloss = 0.0
            drilossdev = 0.0
            conloss = 0.0
            conlossdev = 0.0
            totloss = 0.0
            totlossdev = 0.0

            if "appr_bldg" in dmg_set_df:
                valloss = dmg_set_df["appr_bldg"].astype(float) * dmg_set_df["meandamage"].astype(float) * infl_mult
                vallossdev = dmg_set_df["appr_bldg"].astype(float) * dmg_set_df["mdamagedev"].astype(float) * infl_mult

            bldg_results["strloss"] = valloss.round(2)
            bldg_results["strlossdev"] = vallossdev.round(2)

            result_name = self.get_parameter("result_name")
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

    # def get_non_structural_dmg(self, bldg_nsdmg_set):
    def populate_feature_map(self, nsdmg_map, bldg_nsdmg_set):
        """Get non-structural damage.

        Args:
            nsdmg_map (list): Multiple buildings from input inventory set.
            bldg_nsdmg_set (list): Multiple buildings from input inventory set.

        Returns:
            float: Non structurall building multiplier.

        """
        return (self.infl_factor / 100.0) + 1.0

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
                    'id': 'occupancy_type',
                    'required': False,
                    'description': 'Type of building occupancy type. This variable defines the structural and '
                                   'non-structural damages and the choice of corresponding occupancy multipliers. '
                                   'Values are '
                                   'LOSS, structural building damage'
                                   'ASS, non-structural building damage,'
                                   'DRI, non-structural building damage,'
                                   'CON, non-structural building damage,'
                                   'default is LOSS',
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
                    'description': 'Building mean damage results CSV file',
                    'type': ['ergo:meanDamage']
                },
                {
                    'id': 'building_occupancy',
                    'required': False,
                    'description': 'Building occupancy, use, efacility and multipliers',
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
