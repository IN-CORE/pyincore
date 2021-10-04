# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd

from pyincore import BaseAnalysis


class JoplinEmpiricalRestoration(BaseAnalysis):
    """ Joplin Empirical Restoration Model generates a random realization for the restoration time of
    a building damaged in a tornado event to be restored to a certain functionality level. Functionality
    levels in this model are defined according to Koliou and van de Lindt (2020) and range from Functionality
    Level 4 (FL4, the lowest functionality) to Functionality Level 0 (FL0, full functionality).

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):

        super(JoplinEmpiricalRestoration, self).__init__(incore_client)

    def run(self):
        """ Executes Joplin empirical restoration model analysis.

        Returns:
            bool: True if successful, False otherwise.

        """
        # Get seed
        seed_i = self.get_parameter("seed")

        result_name = self.get_parameter("result_name")

        # Building damage dataset
        building_dmg = self.get_input_dataset("building_dmg").get_dataframe_from_csv(low_memory=False)

        # Get functionality level dataset and create Pandas DataFrame
        func_levels = self.get_input_dataset("functionality_level").get_dataframe_from_csv(low_memory=False)

        # Returns dataframe
        final_inventory = self.get_restoration_days(seed_i, building_dmg, func_levels)
        csv_source = "dataframe"
        self.set_result_csv_data("result", final_inventory, result_name, "dataframe")

        return True

    def get_restoration_days(self, seed, building_dmg, func_levels):
        """ Calculates restoration days.

        Args:
            seed_i (int): Seed for random number generator to ensure replication if run as part
                    of a stochastic analysis, for example in connection with housing unit allocation analysis.
            building_dmg (pd.DataFrame): Building damage dataset with Damage states.
            func_levels (pd.DataFrame): A target functionality level of the building.

        Returns:
            float: Building restoration days.

        """
        iFL = func_levels.iloc[0]["initialFL"]
        tFL = func_levels.iloc[0]["targetFL"]
        # import the initial functionality level of the building
        # and the target functionality level

        restoration_days = 0.0
        if iFL == 4:  # if initial functionality is FL4
            if tFL == 3:  # if target functionality is FL3
                restoration_days = np.random.lognormal(6.13, 0.33, None)
            elif tFL == 2:  # if target functionality is FL2
                restoration_days = np.random.lognormal(6.49, 0.6, None)
            elif tFL == 1:  # if target functionality is FL1
                restoration_days = np.random.lognormal(6.39, 0.48, None)
            elif tFL == 0:  # if target functionality is FL0
                restoration_days = np.random.lognormal(6.60, 0.53, None)
        elif iFL == 3:  # if initial functionality is FL3
            if tFL == 2:  # if target functionality is FL2
                restoration_days = np.random.lognormal(5.56, 0.46, None)
            elif tFL == 1:  # if target functionality is FL1
                restoration_days = np.random.lognormal(5.74, 0.55, None)
            elif tFL == 0:  # if target functionality is FL0
                restoration_days = np.random.lognormal(5.90, 0.60, None)
        elif iFL == 2:  # if initial functionality is FL2
            if tFL == 1:  # if target functionality is FL1
                restoration_days = np.random.lognormal(5.87, 0.35, None)
            elif tFL == 0:  # if target functionality is FL0
                restoration_days = np.random.lognormal(6.06, 0.32, None)
        elif iFL == 1:  # if initial functionality is FL1
            if tFL == 0:  # if target functionality is FL0
                restoration_days = np.random.lognormal(5.90, 0.5, None)

        # Output of the model is restoration_days
        return float(restoration_days)

    def get_spec(self):
        """Get specifications of the Joplin empirical restoration analysis.

        Returns:
            obj: A JSON object of specifications of the Joplin empirical restoration analysis.

        """
        return {
            "name": "joplin-empirical-restoration",
            "description": "Values (in days) for the predicted restoration time of the building.",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "result dataset name",
                    "type": str
                },
                {
                    "id": "seed",
                    "required": False,
                    "description": "Initial seed for the tornado hazard value",
                    "type": int
                }
            ],
            "input_datasets": [
                {
                    "id": "building_dmg",
                    "required": True,
                    "description": "Building damage results CSV file",
                    "type": ["ergo:buildingDamageVer4",
                             "ergo:buildingDamageVer5",
                             "ergo:buildingDamageVer6",
                             "ergo:buildingInventory",
                             "ergo:nsBuildingInventoryDamage",
                             "ergo:nsBuildingInventoryDamageVer2"]
                },
                {
                    "id": "functionality_level",
                    "required": True,
                    "description": "The target functionality level of the building.",
                    "type": ["incore:TargetFunctionalityVer1"]
                }
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "parent_type": "buildings",
                    "description": "A dataset containing results (format: CSV) with values (in days) for the predicted "
                                   "restoration time of the building.",
                    "type": "incore:restorationTime"
                }
            ]
        }
