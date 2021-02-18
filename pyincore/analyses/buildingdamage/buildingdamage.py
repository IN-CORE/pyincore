# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import concurrent.futures
from itertools import repeat

from pyincore import BaseAnalysis, HazardService, \
    FragilityService, AnalysisUtil, GeoUtil
from pyincore.analyses.buildingdamage.buildingutil import BuildingUtil
from pyincore.models.fragilitycurverefactored import FragilityCurveRefactored


class BuildingDamage(BaseAnalysis):
    """Building Damage Analysis calculates the probability of building damage based on
    different hazard type such as earthquake, tsunami, and tornado.

    Args:
        incore_client (IncoreClient): Service authentication.

    """
    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(BuildingDamage, self).__init__(incore_client)

    def run(self):
        """Executes building damage analysis."""
        # Building dataset
        bldg_set = self.get_input_dataset("buildings").get_inventory_reader()

        # Get hazard input
        hazard_dataset_id = self.get_parameter("hazard_id")

        # Hazard type of the exposure
        hazard_type = self.get_parameter("hazard_type")

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = BuildingUtil.DEFAULT_TSUNAMI_MMAX_FRAGILITY_KEY if hazard_type == 'tsunami' else \
                BuildingUtil.DEFAULT_FRAGILITY_KEY
            self.set_parameter("fragility_key", fragility_key)

        user_defined_cpu = 1

        if not self.get_parameter("num_cpu") is None and self.get_parameter("num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self, len(bldg_set), user_defined_cpu)

        avg_bulk_input_size = int(len(bldg_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(bldg_set)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.building_damage_concurrent_future(self.building_damage_analysis_bulk_input, num_workers,
                                                         inventory_args, repeat(hazard_type), repeat(hazard_dataset_id))

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))

        return True

    def building_damage_concurrent_future(self, function_name, parallelism, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            parallelism (int): Number of workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=parallelism) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def building_damage_analysis_bulk_input(self, buildings, hazard_type, hazard_dataset_id):
        """Run analysis for multiple buildings.

        Args:
            buildings (list): Multiple buildings from input inventory set.
            hazard_type (str): Hazard type, either earthquake, tornado, or tsunami.
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """

        fragility_key = self.get_parameter("fragility_key")
        fragility_sets = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), buildings,
                                                           fragility_key)
        values_payload = []
        unmapped_buildings = []
        mapped_buildings = []
        for b in buildings:
            bldg_id = b["id"]
            if bldg_id in fragility_sets:
                location = GeoUtil.get_location(b)
                loc = str(location.y) + "," + str(location.x)
                demands = AnalysisUtil.get_hazard_demand_types(b, fragility_sets[bldg_id], hazard_type)
                units = fragility_sets[bldg_id].demand_units
                value = {
                            "demands": demands,
                            "units": units,
                            "loc": loc
                        }
                values_payload.append(value)
                mapped_buildings.append(b)

            else:
                unmapped_buildings.append(b)

        # not needed anymore as they are already split into mapped and unmapped
        del buildings

        if hazard_type == 'earthquake':
            hazard_vals = self.hazardsvc.post_earthquake_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'tornado':
            hazard_vals = self.hazardsvc.post_tornado_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'tsunami':
            hazard_vals = self.hazardsvc.post_tsunami_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'hurricane':
            hazard_vals = self.hazardsvc.post_hurricane_hazard_values(hazard_dataset_id, values_payload)

        bldg_results = []
        i = 0
        for b in mapped_buildings:
            bldg_result = dict()
            b_id = b["id"]
            num_stories = b['properties']['no_stories']
            selected_fragility_set = fragility_sets[b_id]

            if hazard_type.lower() == "hurricane":
                # TODO: dummy - remove it
                b_haz_vals = str(hazard_vals[i]["hazardValues"][0]) + "," + str(hazard_vals[i]["hazardValues"][1])
                b_demands = ",".join(hazard_vals[i]["demands"])
                b_units = ",".join(hazard_vals[i]["units"])
            else:
                # TODO: remove 0 index to generalize this
                b_haz_vals = hazard_vals[i]["hazardValues"][0]
                b_demands = hazard_vals[i]["demands"][0]
                b_units = hazard_vals[i]["units"][0]

            building_period = selected_fragility_set.fragility_curves[0].get_building_period(num_stories)

            if isinstance(selected_fragility_set.fragility_curves[0], FragilityCurveRefactored):
                hval_dict = dict()
                j = 0
                for d in hazard_vals[i]["demands"]:
                    hval_dict[d] = hazard_vals[i]["hazardValues"][j]
                    j += 1

                building_args = selected_fragility_set.construct_expression_args(b)

                dmg_probability = selected_fragility_set.calculate_limit_state_refactored_w_conversion(
                    hval_dict, **building_args)
                dmg_interval = selected_fragility_set.calculate_damage_interval(
                    dmg_probability, hazard_type=hazard_type, inventory_type="building")
            else:
                dmg_probability = selected_fragility_set.calculate_limit_state_w_conversion(b_haz_vals,
                                                                                            building_period)
                dmg_interval = selected_fragility_set.calculate_damage_interval(dmg_probability)

            bldg_result['guid'] = b['properties']['guid']
            bldg_result.update(dmg_probability)
            bldg_result.update(dmg_interval)
            bldg_result['demandtype'] = b_demands
            bldg_result['demandunits'] = b_units
            bldg_result['hazardval'] = b_haz_vals

            bldg_results.append(bldg_result)
            i += 1

        for b in unmapped_buildings:
            bldg_result = dict()
            bldg_result['guid'] = b['properties']['guid']
            bldg_result['demandtype'] = "none"
            bldg_result['demandunits'] = "none"
            bldg_result['hazardval'] = "none"

            bldg_results.append(bldg_result)

        return bldg_results

    def get_spec(self):
        """Get specifications of the building damage analysis.

        Returns:
            obj: A JSON object of specifications of the building damage analysis.

        """
        return {
            'name': 'building-damage',
            'description': 'building damage analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                },
                {
                    'id': 'hazard_type',
                    'required': True,
                    'description': 'Hazard Type (e.g. earthquake)',
                    'type': str
                },
                {
                    'id': 'hazard_id',
                    'required': True,
                    'description': 'Hazard ID',
                    'type': str
                },
                {
                    'id': 'fragility_key',
                    'required': False,
                    'description': 'Fragility key to use in mapping dataset',
                    'type': str
                },
                {
                    'id': 'use_liquefaction',
                    'required': False,
                    'description': 'Use liquefaction',
                    'type': bool
                },
                {
                    'id': 'use_hazard_uncertainty',
                    'required': False,
                    'description': 'Use hazard uncertainty',
                    'type': bool
                },
                {
                    'id': 'num_cpu',
                    'required': False,
                    'description': 'If using parallel execution, the number of cpus to request',
                    'type': int
                },
            ],
            'input_datasets': [
                {
                    'id': 'buildings',
                    'required': True,
                    'description': 'Building Inventory',
                    'type': ['ergo:buildingInventoryVer4', 'ergo:buildingInventoryVer5',
                             'ergo:buildingInventoryVer6', 'ergo:buildingInventoryVer7'],
                },
                {
                    'id': 'dfr3_mapping_set',
                    'required': True,
                    'description': 'DFR3 Mapping Set Object',
                    'type': ['incore:dfr3MappingSet'],
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'buildings',
                    'description': 'CSV file of building structural damage',
                    'type': 'ergo:buildingDamageVer5'
                }
            ]
        }
