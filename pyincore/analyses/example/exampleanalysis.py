# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import collections
import traceback
import random
from pyincore import BaseAnalysis


class ExampleAnalysis(BaseAnalysis):
    """Example Analysis demonstrates how to use the base analysis class by loading in building data and computing some
    mock damage output and writing the result dataset
    """

    def run(self):
        """Executes building damage analysis."""
        # Building dataset
        bldg_set = self.get_input_dataset("buildings").get_inventory_reader()

        results = []
        # Iterate over the building dataset and compute damage for each
        for building in bldg_set:
            results.append(self.building_damage_analysis(building))

        # Create the result dataset
        self.set_result_csv_data(
            "result", results, name=self.get_parameter("result_name")
        )

        return True

    def building_damage_analysis(self, building):
        """Calculates building damage results for a single building.

        Args:
            building (obj): A JSON mapping of a geometric object from the inventory: current building.

        Returns:
            OrderedDict: A dictionary with building damage values and other data/metadata.

        """
        try:
            # Uncomment this to print building attributes
            # print(building)
            bldg_results = collections.OrderedDict()

            mean_damage = collections.OrderedDict()
            mean_damage["meandamage"] = random.uniform(0.0, 1.0)

            # Add building global id so damage can be linked to building attributes
            bldg_results["guid"] = building["properties"]["guid"]
            # Damage result
            bldg_results.update(mean_damage)

            return bldg_results

        except Exception as e:
            # This prints the type, value and stacktrace of error being handled.
            traceback.print_exc()
            print()
            raise e

    def get_spec(self):
        """Get specifications of the building damage analysis.

        Returns:
            obj: A JSON object of specifications of the building damage analysis.

        """
        return {
            "name": "mock-building-damage",
            "description": "mock-building damage analysis",
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
                    ],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "parent_type": "buildings",
                    "description": "CSV file of building structural damage",
                    "type": "ergo:buildingDamageVer4",
                }
            ],
        }
