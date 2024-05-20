# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd

from pyincore import BaseAnalysis, RepairService
from pyincore.analyses.buildingdamage.buildingutil import BuildingUtil


class BuildingRepair(BaseAnalysis):
    """
    This analysis computes the repair time needed for each building from any damage state. The repair model followed
    the FEMA P-58 approach and was controlled by fragility functions.

    The outputs of this analysis is a CSV file with repair time for simulated damage state at the building level.

    Contributors
        | Science: Wanting Lisa Wang, John W. van de Lindt
        | Implementation: NCSA IN-CORE Dev Team

    Related publications
        Wang, Wanting Lisa, and John W. van de Lindt. "Quantitative Modeling of Residential Building Disaster Recovery
        and Effects of Pre-and Post-event Policies." International Journal of Disaster Risk Reduction (2021): 102259.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        self.repairsvc = RepairService(incore_client)

        super(BuildingRepair, self).__init__(incore_client)

    def run(self):
        """Executes the residential building recovery analysis.

        Returns:
            bool: True if successful, False otherwise.

        """
        result_name = self.get_parameter("result_name")

        buildings = self.get_input_dataset("buildings").get_inventory_reader()
        buildings = list(buildings)
        sample_damage_states = self.get_input_dataset("sample_damage_states").get_dataframe_from_csv(low_memory=False)

        # Returns dataframe
        repair_results = self.recovery_rate(buildings, sample_damage_states)
        self.set_result_csv_data("repair_time", repair_results, result_name, "dataframe")

        return True

    def recovery_rate(self, buildings, sample_damage_states):
        """ Gets repair time required for each building.

        Args:
            buildings (list): List of buildings
            sample_damage_states (pd.DataFrame): Samples' damage states

        Returns:
            pd.DataFrame: Repair time of all buildings for each sample
        """
        seed = self.get_parameter("seed")
        if seed is not None:
            np.random.seed(seed)

        num_samples = self.get_parameter("num_samples")

        repair_key = self.get_parameter("repair_key")
        if repair_key is None:
            repair_key = BuildingUtil.DEFAULT_REPAIR_KEY
            self.set_parameter("repair_key", repair_key)
        repair_sets = self.repairsvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), buildings, repair_key)
        repair_sets_by_guid = {}  # get repair sets by guid so they can be mapped with output of monte carlo

        # This is sort of a workaround until we define Repair Curve models and abstract this out there
        for i, b in enumerate(buildings):
            repair_sets_by_guid[b["properties"]['guid']] = repair_sets[str(i)]

        for index, row in sample_damage_states.iterrows():
            # Obtain the damage states
            mapped_repair = repair_sets_by_guid[row['guid']]
            samples_mcs = row['sample_damage_states'].split(",")

            # Use a lambda to obtain the damage state in numeric form. Note that since damage states are single digits,
            # it suffices to look at the last character and convert into an integer value. Do this computation once
            # per household only.
            samples_mcs_ds = list(map(lambda x: int(x[-1]), samples_mcs))

            # Now, perform the two nested loops, using the indexing function to simplify the syntax.
            for i in range(0, len(samples_mcs)):
                state = samples_mcs_ds[i]

                percent_func = np.random.random(num_samples)
                # NOTE: Even though the kwarg name is "repair_time", it actually takes percent of functionality. DFR3
                # system currently doesn't have a way to represent the name correctly when calculating the inverse.
                repair_time = mapped_repair.repair_curves[state].solve_curve_for_inverse(
                    hazard_values={}, curve_parameters=mapped_repair.curve_parameters, **{"repair_time": percent_func}
                ) / 7
                print(repair_time)

        return repair_time

    def get_spec(self):
        """Get specifications of the residential building recovery analysis.

        Returns:
            obj: A JSON object of specifications of the residential building recovery analysis.

        """
        return {
            'name': 'building repair',
            'description': 'calculate building repair time',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'name of the result',
                    'type': str
                },
                {
                    'id': 'repair_key',
                    'required': False,
                    'description': 'Repair key to use in mapping dataset',
                    'type': str
                },
                {
                    'id': 'seed',
                    'required': False,
                    'description': 'Initial seed for the probabilistic model',
                    'type': int
                },
                {
                    'id': 'num_samples',
                    'required': True,
                    'description': 'Number of sample scenarios',
                    'type': int
                },
            ],
            'input_datasets': [
                {
                    'id': 'buildings',
                    'required': True,
                    'description': 'Building Inventory',
                    'type': ['ergo:buildingInventoryVer4', 'ergo:buildingInventoryVer5', 'ergo:buildingInventoryVer6',
                             'ergo:buildingInventoryVer7']
                },
                {
                    'id': 'dfr3_mapping_set',
                    'required': True,
                    'description': 'DFR3 Mapping Set Object',
                    'type': ['incore:dfr3MappingSet'],
                },
                {
                    'id': 'sample_damage_states',
                    'required': True,
                    'description': 'Sample damage states',
                    'type': ['incore:sampleDamageState']
                },
            ],
            'output_datasets': [
                {
                    'id': 'repair_time',
                    'description': 'CSV file of building repair times',
                    'type': 'incore:buildingRepairTime'
                }
            ]
        }
