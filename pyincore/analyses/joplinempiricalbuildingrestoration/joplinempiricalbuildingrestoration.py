# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd

from pyincore import BaseAnalysis
from pyincore.analyses.joplinempiricalbuildingrestoration.joplinempirrestor_util import (
    JoplinEmpirRestorUtil,
)


class JoplinEmpiricalBuildingRestoration(BaseAnalysis):
    """Joplin Empirical Building Restoration Model generates a random realization for the restoration time of
    a building damaged in a tornado event to be restored to a certain functionality level. Functionality
    levels in this model are defined according to Koliou and van de Lindt (2020) and range from Functionality
    Level 4 (FL4, the lowest functionality) to Functionality Level 0 (FL0, full functionality).

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(JoplinEmpiricalBuildingRestoration, self).__init__(incore_client)

    def run(self):
        """Executes Joplin empirical building restoration model analysis.

        Returns:
            bool: True if successful, False otherwise.

        """
        # Get seed
        seed_i = self.get_parameter("seed")
        target_fl = self.get_parameter("target_functionality_level")

        result_name = self.get_parameter("result_name")

        # Building dataset
        building_set = self.get_input_dataset(
            "buildings"
        ).get_dataframe_from_shapefile()
        # Building damage dataset
        building_dmg = self.get_input_dataset("building_dmg").get_dataframe_from_csv(
            low_memory=False
        )
        # Building functionality target level
        building_target_fl = self.get_input_dataset("building_functionality_level")
        if building_target_fl is not None:
            building_target_fl = building_target_fl.get_dataframe_from_csv(
                low_memory=False
            )
        else:
            building_target_fl = None

        # merge and filter out archetypes > 5
        building_dmg_all = pd.merge(
            building_dmg, building_set, how="left", on="guid", copy=True, validate="1:1"
        )
        building_dmg_5 = building_dmg_all[
            ["guid", "archetype", "LS_0", "LS_1", "LS_2", "haz_expose"]
        ].copy()
        building_func_5 = building_dmg_5[building_dmg_all["archetype"] <= 5]

        building_func = building_func_5[
            ["guid", "LS_0", "LS_1", "LS_2", "haz_expose"]
        ].copy()
        building_func["targetFL"] = target_fl

        if building_target_fl is not None:
            building_func = pd.merge(
                building_func,
                building_target_fl,
                how="left",
                on="guid",
                copy=True,
                validate="1:1",
            )
            # Replace NaN value from targetFL_y with targetFL_x value
            building_func["targetFL"] = building_func["targetFL_y"].fillna(
                building_func["targetFL_x"]
            )
            # Drop merged columns
            building_func = building_func.drop(["targetFL_x", "targetFL_y"], axis=1)
            building_func = building_func.astype({"targetFL": "int64"})

        initial_func_level, restoration_days = self.get_restoration_days(
            seed_i, building_func
        )
        building_func["initialFL"] = initial_func_level
        building_func["restorDays"] = restoration_days

        building_func_fin = building_func[
            ["guid", "initialFL", "targetFL", "restorDays"]
        ]
        csv_source = "dataframe"
        self.set_result_csv_data("result", building_func_fin, result_name, csv_source)

        return True

    def get_restoration_days(self, seed_i, building_func):
        """Calculates restoration days.

        Args:
            seed_i (int): Seed for random number generator to ensure replication if run as part
                of a stochastic analysis, for example in connection with housing unit allocation analysis.
            building_func (pd.DataFrame): Building damage dataset with guid, limit states, hazard exposure
                and a target level column.

        Returns:
            np.array: Initial functionality level based on damage state
            np.array: Building restoration days.

        """
        fl_coef = JoplinEmpirRestorUtil.FL_COEF

        hazard_value = building_func[["haz_expose"]].to_numpy() != "no"
        hazard_value = hazard_value.flatten()

        bdnp = building_func[["LS_0", "LS_1", "LS_2"]].to_numpy()

        # generate a random number between 0 and 1 and see where in boundaries it locates and use it to assign FL,
        # for each building
        rnd_num = np.random.uniform(
            0,
            1,
            (
                len(
                    building_func.index,
                )
            ),
        )
        bdnp_init = np.zeros(
            len(
                building_func.index,
            )
        ).astype(
            int
        )  # first, set all to 0
        bdnp_init = np.where(
            rnd_num < bdnp[:, 0], 1, bdnp_init
        )  # if rnd_num < LS_0 set to 1
        bdnp_init = np.where(
            rnd_num < bdnp[:, 1], 2, bdnp_init
        )  # if rnd_num < LS_0 set to 2
        bdnp_init = np.where(
            rnd_num < bdnp[:, 2], 3, bdnp_init
        )  # if rnd_num < LS_0 set to 3

        bdnp_target = building_func["targetFL"].to_numpy()

        means = fl_coef[bdnp_init, bdnp_target, 0]
        sigmas = fl_coef[bdnp_init, bdnp_target, 1]

        np.random.seed(seed_i)
        rest_days = np.random.lognormal(means, sigmas)

        # only when exposed to hazard, otherwise no damage and restoration = 0
        restoration_days = np.where(hazard_value, rest_days, 0).astype(int)
        # F1-F4 notation
        bdnp_init = bdnp_init + 1
        # F0 where not exposed to hazard
        initial_func_level = np.where(hazard_value, bdnp_init, 0).astype(int)

        # Output of the model is restoration_days
        return initial_func_level, restoration_days

    def get_spec(self):
        """Get specifications of the Joplin empirical building restoration analysis.

        Returns:
            obj: A JSON object of specifications of the Joplin empirical building restoration analysis.

        """
        return {
            "name": "joplin-empirical-building-restoration",
            "description": "Values (in days) for the predicted restoration time of the building.",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "result dataset name",
                    "type": str,
                },
                {
                    "id": "target_functionality_level",
                    "required": False,
                    "description": "Target functionality level for all infrastructure",
                    "type": int,
                },
                {
                    "id": "seed",
                    "required": False,
                    "description": "Initial seed for the tornado hazard value",
                    "type": int,
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
                    "id": "building_dmg",
                    "required": True,
                    "description": "Building damage results CSV file",
                    "type": [
                        "ergo:buildingDamageVer4",
                        "ergo:buildingDamageVer5",
                        "ergo:buildingDamageVer6",
                        "ergo:buildingInventory",
                        "ergo:nsBuildingInventoryDamage",
                        "ergo:nsBuildingInventoryDamageVer2",
                        "ergo:nsBuildingInventoryDamageVer3",
                        "ergo:nsBuildingInventoryDamageVer4",
                    ],
                },
                {
                    "id": "building_functionality_level",
                    "required": False,
                    "description": "Functionality level per building. The target level defaults "
                    "to target_functionality_level parameter if building not in the dataset",
                    "type": ["incore:buildingFuncTargetVer1"],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "parent_type": "buildings",
                    "description": "A dataset containing results (format: CSV) with values (in days) for the predicted "
                    "restoration time of the building.",
                    "type": "incore:restorationTime",
                }
            ],
        }
