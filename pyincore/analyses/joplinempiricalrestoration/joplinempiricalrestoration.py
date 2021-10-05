# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd

from pyincore import BaseAnalysis
from pyincore.analyses.joplinempiricalrestoration.joplinempirrestor_util import JoplinEmpirRestorUtil


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
        targetFL = self.get_parameter("target_functionality_level")

        result_name = self.get_parameter("result_name")

        # Building damage dataset
        building_dmg = self.get_input_dataset("building_dmg").get_dataframe_from_csv(low_memory=False)

        building_func = building_dmg[["guid"]].copy()
        building_func["targetFL"] = targetFL

        initial_func_level, restoration_days = self.get_restoration_days(seed_i, building_dmg, building_func["targetFL"])
        building_func["initialFL"] = initial_func_level
        building_func["restorDays"] = restoration_days

        building_func_fin = building_func[["guid", "initialFL", "targetFL", "restorDays"]]
        csv_source = "dataframe"
        self.set_result_csv_data("result", building_func_fin, result_name, csv_source)

        return True

    def get_restoration_days(self, seed_i, building_dmg, target_func_levels):
        """ Calculates restoration days.

        Args:
            seed_i (int): Seed for random number generator to ensure replication if run as part
                    of a stochastic analysis, for example in connection with housing unit allocation analysis.
            building_dmg (pd.DataFrame): Building damage dataset with Damage states.
            target_func_levels (pd.DataFrame): A target functionality level of the building.

        Returns:
            np.array: Initial functionality level based on damage state
            np.array: Building restoration days.

        """
        fl_coef = JoplinEmpirRestorUtil.FL_COEF

        hazard_value = building_dmg[["hazardval"]].to_numpy() != 0
        hazard_value = hazard_value.flatten()

        bdnp = building_dmg[["DS_0", "DS_1", "DS_2", "DS_3"]].to_numpy()
        # get index of Damage state of max probability
        bdnp_init = np.argmax(bdnp, axis=1)
        bdnp_target = target_func_levels.to_numpy()

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
                    "id": "target_functionality_level",
                    "required": False,
                    "description": "Target functionality level for all infrastructure",
                    "type": int
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
                    "required": False,
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
