# Copyright (c) 2024 University of Illinois and others. All rights reserved.

# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd
from pyincore import BaseAnalysis
from pyincore.utils.dataprocessutil import DataProcessUtil


class BuyoutDecision(BaseAnalysis):
    """A framework to select households for buyout based on past and future flood damaged.

    Args:
    incore_client(IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(BuyoutDecision, self).__init__(incore_client)

    def run(self):
        # Get input parameters
        fema_buyout_cap = self.get_parameter("fema_buyout_cap")
        residential_archetypes = self.get_parameter("residential_archetypes")

        # Get input datasets
        past_building_damage = self.get_input_dataset(
            "past_building_damage"
        ).get_dataframe_from_csv(low_memory=False)
        future_building_damage = self.get_input_dataset(
            "future_building_damage"
        ).get_dataframe_from_csv(low_memory=False)

        building_inventory = self.get_input_dataset(
            "buildings"
        ).get_dataframe_from_shapefile()

        hua = self.get_input_dataset("housing_unit_allocation").get_dataframe_from_csv(
            low_memory=False
        )
        pop_dislocation = self.get_input_dataset(
            "population_dislocation"
        ).get_dataframe_from_csv(low_memory=False)

        buyout_decision_df = self.buyout_decision(
            past_building_damage,
            future_building_damage,
            building_inventory,
            hua,
            pop_dislocation,
            fema_buyout_cap,
            residential_archetypes,
        )
        # Create the result dataset
        self.set_result_csv_data(
            "result",
            buyout_decision_df,
            self.get_parameter("result_name") + "_loss",
            "dataframe",
        )

    def buyout_decision(
        self,
        past_building_damage,
        future_building_damage,
        building_inventory,
        hua,
        pop_dislocation,
        fema_buyout_cap,
        residential_archetpyes,
    ):
        """Select households for buyout based on past and future flood damaged.

        Args:
        past_building_damage (DataFrame): Past building damage.
        future_building_damage (DataFrame):  Future event building damage.
        building_inventory (DataFrame): Building inventory.
        hua (DataFrame): Housing unit allocation.
        pop_dislocation (DataFrame): Population dislocation from past hazard event.
        fema_buyout_cap (float): FEMA buyout cap.
        residential_archetpyes (list): Residential archetypes.

        Returns:
        buyout_decision_df (DataFrame): A dataframe with buyout decision for each household.
        """

        past_building_max_damage = DataProcessUtil.get_max_damage_state(
            past_building_damage
        )
        future_building_max_damage = DataProcessUtil.get_max_damage_state(
            future_building_damage
        )

        # Criterion 1: Filter only residential buildings with damage state DS3 from past building damage
        buyout_inventory = pd.merge(
            building_inventory, past_building_max_damage, on="guid", how="outer"
        )
        buyout_inventory = buyout_inventory[
            buyout_inventory["arch_wind"].isin(residential_archetpyes)
            & (buyout_inventory["max_state"] == "DS_3")
        ]
        buyout_inventory.rename(
            columns={"max_state": "max_state_past_damage"}, inplace=True
        )

        # Criterion 2: Filter only residential buildings with damage state DS3 from predicted future building damage
        buyout_inventory = pd.merge(
            buyout_inventory, future_building_max_damage, on="guid", how="inner"
        )
        buyout_inventory = buyout_inventory[buyout_inventory["max_state"] == "DS_3"]
        buyout_inventory.rename(
            columns={"max_state": "max_state_future_damage"}, inplace=True
        )

        # Criterion 3: Fall within the FEMA buyout cap
        buyout_inventory = buyout_inventory[
            buyout_inventory["appr_bldg"] <= fema_buyout_cap
        ]
        buyout_inventory = buyout_inventory[
            [
                "guid",
                "appr_bldg",
                "max_state_future_damage",
                "max_state_past_damage",
                "geometry",
            ]
        ]

        # Criterion 4: Use HUA to filter out buildings with 0 occupants
        buyout_inventory = pd.merge(buyout_inventory, hua, on="guid", how="left")
        buyout_inventory = buyout_inventory[
            (buyout_inventory["numprec"] != 0) & (~buyout_inventory["numprec"].isna())
        ]

        # Removing any rows with NAN values in column "Race"
        buyout_inventory = buyout_inventory.dropna(subset=["race"])

        # Merging with population dislocation
        buyout_inventory = pd.merge(
            buyout_inventory,
            pop_dislocation[["huid", "dislocated"]],
            on="huid",
            how="left",
        )

        # Create a new column showing the appraisal value of each building ('appr_bldg' divided by the number of times
        # a guid is repeated)
        # For the instances that a structure has more than one housing units.
        buyout_inventory["count"] = buyout_inventory.groupby("guid")["guid"].transform(
            "count"
        )
        buyout_inventory["housing_unit_appraisal_value"] = (
            buyout_inventory["appr_bldg"] / buyout_inventory["count"]
        )

        # Cleaning the dataframe
        buyout_inventory.drop(
            [
                "blockid",
                "bgid",
                "tractid",
                "FIPScounty",
                "gqtype",
                "BLOCKID10_str",
                "placeNAME10",
                "geometry_y",
            ],
            axis=1,
            inplace=True,
        )
        buyout_inventory.rename(
            columns={
                "appr_bldg": "building_appraisal_value",
                "ownershp": "ownership",
                "dislocated_combined_dmg": "dislocated",
                "count": "number_of_housing_units",
                "geometry_x": "geometry",
            },
            inplace=True,
        )
        buyout_inventory = buyout_inventory[
            [
                "guid",
                "huid",
                "building_appraisal_value",
                "housing_unit_appraisal_value",
                "geometry",
                "number_of_housing_units",
                "numprec",
                "ownership",
                "race",
                "hispan",
                "family",
                "vacancy",
                "incomegroup",
                "hhinc",
                "randincome",
                "poverty",
                "huestimate",
                "dislocated",
                "max_state_future_damage",
                "max_state_past_damage",
                "x",
                "y",
            ]
        ]

        return buyout_inventory

    def get_spec(self):
        return {
            "name": "buyout-decision",
            "description": "Buyout decision framework",
            "input_parameters": [
                {
                    "id": "fema_buyout_cap",
                    "required": True,
                    "description": "FEMA buyout cap",
                    "type": float,
                },
                {
                    "id": "residential_archetypes",
                    "required": True,
                    "description": "Residential archetypes",
                    "type": list,
                },
                {
                    "id": "result_name",
                    "required": True,
                    "description": "Result name",
                    "type": str,
                },
            ],
            "input_datasets": [
                {
                    "id": "past_building_damage",
                    "required": True,
                    "description": "Building Damage Results",
                    "type": ["ergo:buildingDamageVer6"],
                },
                {
                    "id": "future_building_damage",
                    "required": True,
                    "description": "Building Damage Results",
                    "type": ["ergo:buildingDamageVer6"],
                },
                {
                    "id": "buildings",
                    "required": True,
                    "description": "Building Inventory",
                    "type": [
                        "ergo:buildingInventoryVer4",
                        "ergo:buildingInventoryVer5",
                        "ergo:buildingInventoryVer6",
                        "ergo:buildingInventoryVer7",
                    ],
                },
                {
                    "id": "housing_unit_allocation",
                    "required": True,
                    "description": "A csv file with the merged dataset of the inputs, aka Probabilistic"
                    "House Unit Allocation",
                    "type": ["incore:housingUnitAllocation"],
                },
                {
                    "id": "population_dislocation",
                    "required": True,
                    "description": "Population Dislocation from past hazard event",
                    "type": ["incore:popDislocation"],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "label": "Buyout Decision Results",
                    "description": "Buyout Decision Results",
                    "type": ["incore:buyoutDecision"],
                }
            ],
        }
