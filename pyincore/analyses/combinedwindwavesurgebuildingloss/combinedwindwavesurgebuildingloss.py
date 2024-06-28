# Copyright (c) 2023 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd
from pyincore import BaseAnalysis
import numpy as np


class CombinedWindWaveSurgeBuildingLoss(BaseAnalysis):
    """
    This analysis computes the building structural and content loss from wind, flood and surge-wave damage

    Contributors
        | Science: Omar Nofal, John W. van de Lindt, Trung Do, Guirong Yan, Sara Hamideh, Daniel Cox, Joel Dietrich
        | Implementation: Jiate Li, Chris Navarro and NCSA IN-CORE Dev Team

    Related publications
        Nofal, Omar & Lindt, John & Do, Trung & Yan, Guirong & Hamideh, Sara & Cox, Daniel & Dietrich, Joel. (2021).
        Methodology for Regional Multi-Hazard Hurricane Damage and Risk Assessment. Journal of Structural Engineering.
        147. 04021185. 10.1061/(ASCE)ST.1943-541X.0003144.

    Args:
        incore_client (IncoreClient): Service authentication.
    """

    def __init__(self, incore_client):
        super(CombinedWindWaveSurgeBuildingLoss, self).__init__(incore_client)

    def run(self):
        """Executes combined wind, wave, surge building loss analysis."""

        # Read buildings
        buildings = self.get_input_dataset("buildings").get_dataframe_from_shapefile()

        # Read Building wind damage
        wind_damage = self.get_input_dataset("wind_damage").get_dataframe_from_csv()

        # Read Building surge-wave damage
        surge_wave_damage = self.get_input_dataset(
            "surge_wave_damage"
        ).get_dataframe_from_csv()

        # Read Building flood damage
        flood_damage = self.get_input_dataset("flood_damage").get_dataframe_from_csv()

        # Read cumulative replacement cost ratio of building content
        content_cost = self.get_input_dataset("content_cost").get_dataframe_from_csv()

        # Read cumulative replacement cost ratio of structural damage
        structure_cost = self.get_input_dataset(
            "structural_cost"
        ).get_dataframe_from_csv()

        combined_loss = self.get_combined_loss(
            wind_damage,
            surge_wave_damage,
            flood_damage,
            buildings,
            content_cost,
            structure_cost,
        )

        # Create the result dataset
        self.set_result_csv_data(
            "result",
            combined_loss,
            self.get_parameter("result_name") + "_loss",
            "dataframe",
        )

        return True

    def get_combined_loss(
        self,
        wind_dmg: pd.DataFrame,
        sw_dmg: pd.DataFrame,
        flood_dmg: pd.DataFrame,
        buildings: pd.DataFrame,
        content_cost: pd.DataFrame,
        structure_cost: pd.DataFrame,
    ):
        """Calculates structural and content loss from wind, surge-wave and flood damage

        Args:
            wind_dmg (pd.DataFrame): Table of wind damage for the building inventory
            sw_dmg (pd.DataFrame): Table of surge-wave damage for the building inventory
            flood_dmg (pd.DataFrame): Table of flood damage for the building inventory
            buildings (pd.DataFrame): Table of building attributes
            content_cost (pd.DataFrame): Table of content cost ratios for each archetype
            structure_cost (pd.DataFrame): Table of structural cost ratio for each archetype and loss type

        Returns:
            pd.DataFrame: An table of structural and content loss for each building

        """
        # Rename the columns so there are no overlapping names among the hazard damage states
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

        # Combine all three sets of damages into a single data frame
        combined_df = pd.merge(
            pd.merge(wind_dmg, sw_dmg, on="guid"), flood_dmg, on="guid"
        )

        # Add the flood archetype to the combined damage since this is used to find loss multipliers
        new_combined_df = pd.merge(
            combined_df, buildings[["guid", "arch_flood"]], on="guid"
        )

        # Create a result data frame for the loss calculations
        loss_df = new_combined_df[["guid"]].copy()

        # Compute content and structural loss
        loss_df["cont_loss"] = new_combined_df.apply(
            lambda row: np.dot(
                row[["f_DS_0", "f_DS_1", "f_DS_2"]],
                content_cost.iloc[int(row["arch_flood"] - 1), 1:4],
            ),
            axis=1,
        )

        loss_df["roof_loss"] = new_combined_df.apply(
            lambda row: np.dot(
                row[["w_DS_0", "w_DS_1", "w_DS_2", "w_DS_3"]],
                np.array([0.15, 0.5, 0.75, 1]),
            )
            * structure_cost.loc[int(row["arch_flood"] - 1), "Roofing"],
            axis=1,
        )

        loss_df["ff_loss"] = new_combined_df.apply(
            lambda row: np.dot(
                row[["sw_DS_0", "sw_DS_1", "sw_DS_2", "sw_DS_3"]],
                np.array([0.1, 0.5, 0.75, 1]),
            )
            * structure_cost.loc[int(row["arch_flood"] - 1), "Flooring and Foundation"],
            axis=1,
        )

        # Computes frame loss from the dominant hazard between wind and surge-wave intensities
        def compute_frame_loss(row):
            if row["w_DS_3"] >= row["sw_DS_3"]:
                return (
                    np.dot(
                        row[["w_DS_0", "w_DS_1", "w_DS_2", "w_DS_3"]],
                        np.array([0.25, 0.5, 0.75, 1]),
                    )
                    * structure_cost.loc[int(row["arch_flood"] - 1), "Wood Framing"]
                )
            elif row["sw_DS_3"] > row["w_DS_3"]:
                return (
                    np.dot(
                        row[["sw_DS_0", "sw_DS_1", "sw_DS_2", "sw_DS_3"]],
                        np.array([0.25, 0.5, 0.75, 1]),
                    )
                    * structure_cost.loc[int(row["arch_flood"] - 1), "Wood Framing"]
                )
            else:
                # If one or both are nan, they can't be compared
                if pd.isnull(row["sw_DS_3"]) and pd.isnull(row["w_DS_3"]):
                    return 0
                elif not pd.isnull(row["sw_DS_3"]):
                    return (
                        np.dot(
                            row[["sw_DS_0", "sw_DS_1", "sw_DS_2", "sw_DS_3"]],
                            np.array([0.25, 0.5, 0.75, 1]),
                        )
                        * structure_cost.loc[int(row["arch_flood"] - 1), "Wood Framing"]
                    )
                else:
                    return (
                        np.dot(
                            row[["w_DS_0", "w_DS_1", "w_DS_2", "w_DS_3"]],
                            np.array([0.25, 0.5, 0.75, 1]),
                        )
                        * structure_cost.loc[int(row["arch_flood"] - 1), "Wood Framing"]
                    )

        loss_df["frame_loss"] = new_combined_df.apply(
            lambda row: compute_frame_loss(row), axis=1
        )

        # Fill NA values with 0 otherwise we can't compute the total loss since empty are NaN values and won't add
        loss_df.fillna(0, inplace=True)
        loss_df["total_loss"] = loss_df.apply(
            lambda row: row["cont_loss"]
            + row["frame_loss"]
            + row["roof_loss"]
            + row["ff_loss"],
            axis=1,
        )

        return loss_df

    def get_spec(self):
        """Get specifications of the combined wind, wave, and surge building loss analysis.

        Returns:
            obj: A JSON object of specifications of the combined wind, wave, and surge building damage analysis.

        """
        return {
            "name": "combined-wind-wave-surge-building-loss",
            "description": "Combined wind wave and surge building loss analysis",
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
                {
                    "id": "structural_cost",
                    "required": True,
                    "description": "Structural cost ratio for each archetype and loss type",
                    "type": ["incore:structuralCostRatio"],
                },
                {
                    "id": "content_cost",
                    "required": True,
                    "description": "Content cost ratio for each archetype and damage state",
                    "type": ["incore:contentCostRatio"],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "parent_type": "buildings",
                    "description": "CSV file of building structural and content loss",
                    "type": "incore:buildingLoss",
                }
            ],
        }
