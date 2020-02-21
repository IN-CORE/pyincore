# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import collections
import concurrent.futures
import traceback
from itertools import repeat

from pyincore import BaseAnalysis, HazardService, FragilityService, \
    AnalysisUtil, GeoUtil
from pyincore.analyses.buildingdamage.buildingutil import BuildingUtil

class BuildingDamagePlus(BaseAnalysis):
    """Building Damage Analysis calculates the probability of building damage based on
    different hazard type such as earthquake, tsunami and tornado by calling fragility
    and hazard services.

    Args:
        incore_client (IncoreClient): Service authentication.

    """
    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(BuildingDamagePlus, self).__init__(incore_client)

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
            hazard_type (str): A hazard type of the hazard exposure.
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        result = []
        fragility_key = self.get_parameter("fragility_key")

        fragility_sets = dict()
        fragility_sets[fragility_key] = self.fragilitysvc.map_inventory(
            self.get_parameter("mapping_id"), buildings, fragility_key)

        grouped_buildings = dict()
        bldg_results = []
        list_buildings = buildings

        buildings = dict()
        # Converting list of buildings into a dictionary for ease of reference
        for b in list_buildings:
            buildings[b["id"]] = b

        list_buildings = None  # Clear as it's not needed anymore

        # Create grouped list of buildings by combination of demand type and demand unit
        for frg_key, bldgs in fragility_sets.items():
            for bldg_id, frag in bldgs.items():
                building = buildings[bldg_id]
                fragility_set = fragility_sets[fragility_key][bldg_id]

                # TODO include liquefaction and hazard uncertainty
                hazard_demand_type = BuildingUtil.get_hazard_demand_type(building, fragility_set,
                    hazard_type)
                demand_type = hazard_demand_type
                demand_units = frag.get("demandUnits")
                tpl = (demand_type, demand_units)

                grouped_buildings.setdefault(tpl, []).append(bldg_id)

        # print(grouped_buildings)

        for demand, grouped_bldgs in grouped_buildings.items():

            input_demand_type = demand[0]
            input_demand_units = demand[1]

            # For every group of unique demand and demand unit, call the end-point once
            bldg_chunks = list(AnalysisUtil.chunks(grouped_bldgs, 50))
            for bldgs in bldg_chunks:
                points = []
                for bldg_id in bldgs:
                    location = GeoUtil.get_location(buildings[bldg_id])
                    points.append(str(location.y) + "," + str(location.x))

                if hazard_type == 'earthquake':
                    hazard_vals = self.hazardsvc.get_earthquake_hazard_values(hazard_dataset_id, input_demand_type, input_demand_units, points)
                elif hazard_type == 'tornado':
                    hazard_vals = self.hazardsvc.get_tornado_hazard_values(hazard_dataset_id, input_demand_units, points)
                elif hazard_type == 'tsunami':
                    hazard_vals = self.hazardsvc.get_tsunami_hazard_values(hazard_dataset_id, input_demand_type, input_demand_units, points)
                elif hazard_type == 'hurricane':
                    # TODO implement hurricane
                    print("hurricane not yet implemented")

                i = 0
                # Parse the batch hazard value results and map them back to the building and fragility.
                # This is a potential pitfall as we are relying on the order of the returned results

                for bldg_id in bldgs:
                    bldg_result = collections.OrderedDict()
                    building = buildings[bldg_id]
                    hazard_val = hazard_vals[i]['hazardValue']
                    num_stories = building['properties']['no_stories']
                    fragility_set = fragility_sets[fragility_key][bldg_id]
                    building_period = AnalysisUtil.get_building_period(num_stories, fragility_set)

                    dmg_probability = AnalysisUtil.calculate_limit_state(fragility_set, hazard_val,
                        building_period)
                    dmg_interval = AnalysisUtil.calculate_damage_interval(dmg_probability)

                    bldg_result['guid'] = building['properties']['guid']
                    bldg_result.update(dmg_probability)
                    bldg_result.update(dmg_interval)
                    # TODO: It might be better to use the applied demand type instead of what's
                    #  specified in the fragility? 0.2 SA returned from API instead of 0.24 Sa
                    bldg_result['demandtype'] = input_demand_type
                    bldg_result['demandunits'] = input_demand_units
                    bldg_result['hazardval'] = hazard_val

                    bldg_results.append(bldg_result)
                    del buildings[bldg_id] # remove processed buildings
                    i = i + 1

        for unmapped_bldg_id,unmapped_bldg in buildings.items():
            unmapped_bldg_result = collections.OrderedDict()
            unmapped_bldg_result['guid'] = unmapped_bldg['properties']['guid']
            unmapped_bldg_result['demandtype'] = "NA"
            unmapped_bldg_result['demandunits'] = "NA"
            unmapped_bldg_result['hazardval'] = "NA"  # TODO: What's a good default? use 0?
            bldg_results.append(unmapped_bldg_result)

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
                    'id': 'mapping_id',
                    'required': True,
                    'description': 'Fragility mapping dataset',
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
                    'type': ['ergo:buildingInventoryVer4', 'ergo:buildingInventoryVer5', 'ergo:buildingInventoryVer6'],
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'buildings',
                    'description': 'CSV file of building structural damage',
                    'type': 'ergo:buildingDamageVer4'
                }
            ]
        }
