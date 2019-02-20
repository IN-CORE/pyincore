# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import collections
from pyincore.analyses.buildingdamage.buildingutil import BuildingUtil
import concurrent.futures
import traceback
from itertools import repeat

from pyincore import BaseAnalysis, HazardService, FragilityService, AnalysisUtil, GeoUtil


class BuildingDamage(BaseAnalysis):
    """Building Damage Analysis calculates the probability of building damage based on
    different hazard type such as earthquake, tsunami and tornado by calling fragility
    and hazard services.

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

        dmg_ratio_csv = self.get_input_dataset("dmg_ratios").get_csv_reader()
        dmg_ratio_tbl = AnalysisUtil.get_csv_table_rows(dmg_ratio_csv)

        # Get hazard input
        hazard_dataset_id = self.get_parameter("hazard_id")

        # Hazard type of the exposure
        hazard_type = self.get_parameter("hazard_type")

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None and not hazard_type == 'tsunami':
            fragility_key = BuildingUtil.DEFAULT_FRAGILITY_KEY
            self.set_parameter("fragility_key", fragility_key)
        else:
            fragility_key = BuildingUtil.DEFAULT_TSUNAMI_MMAX_FRAGILITY_KEY
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
                                                         inventory_args, repeat(hazard_type), repeat(hazard_dataset_id),
                                                         repeat(dmg_ratio_tbl))

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

    def building_damage_analysis_bulk_input(self, buildings, hazard_type, hazard_dataset_id, dmg_ratio_tbl):
        """Run analysis for multiple buildings.

        Args:
            buildings (list): Multiple buildings from input inventory set.
            hazard_type (str): A hazard type of the hazard exposure.
            hazard_dataset_id (str): An id of the hazard exposure.
            dmg_ratio_tbl (obj): A damage ratio table, including weights to compute mean damage.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        result = []
        fragility_key = self.get_parameter("fragility_key")

        fragility_sets = dict()
        fragility_sets[fragility_key] = self.fragilitysvc.map_fragilities(self.get_parameter("mapping_id"), buildings,
                                                                          fragility_key)

        if hazard_type == 'tsunami':
            other_fragility_sets = self.fragilitysvc.map_fragilities(self.get_parameter("mapping_id"), buildings,
                                                                     BuildingUtil.DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY)
            fragility_sets[BuildingUtil.DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY] = other_fragility_sets

        for building in buildings:
            fragility_set = dict()
            if building["id"] in fragility_sets[fragility_key]:
                fragility_set[fragility_key] = fragility_sets[fragility_key][building["id"]]

            if hazard_type == 'tsunami' and building["id"] in \
                    fragility_sets[BuildingUtil.DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY]:
                other_fragility_set = fragility_sets[BuildingUtil.DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY][building["id"]]
                fragility_set[BuildingUtil.DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY] = other_fragility_set

            result.append(self.building_damage_analysis(building, dmg_ratio_tbl, fragility_set, hazard_dataset_id,
                                                        hazard_type))

        return result

    def building_damage_analysis(self, building, dmg_ratio_tbl, fragility_set, hazard_dataset_id, hazard_type):
        """Calculates building damage results for a single building.

        Args:
            building (obj): A JSON mapping of a geometric object from the inventory: current building.
            dmg_ratio_tbl (obj): A table of damage ratios for mean damage.
            fragility_set (obj): A JSON description of fragility assigned to the building.
            hazard_dataset_id (str): A hazard dataset to use.
            hazard_type (str): A hazard type of the hazard exposure.

        Returns:
            OrderedDict: A dictionary with building damage values and other data/metadata.

        """
        try:
            bldg_results = collections.OrderedDict()

            hazard_val = 0.0
            demand_type = "None"

            dmg_probability = collections.OrderedDict()
            dmg_interval = collections.OrderedDict()
            mean_damage = collections.OrderedDict()
            mean_damage['meandamage'] = 0.0
            mean_damage_dev = collections.OrderedDict()
            mean_damage_dev['mdamagedev'] = 0.0

            if bool(fragility_set):
                location = GeoUtil.get_location(building)
                fragility_key = self.get_parameter("fragility_key")
                local_fragility_set = fragility_set[fragility_key]
                if hazard_type == 'earthquake':
                    # TODO include liquefaction and hazard uncertainty
                    hazard_demand_type = BuildingUtil.get_hazard_demand_type(building, local_fragility_set, hazard_type)
                    demand_units = local_fragility_set['demandUnits']
                    hazard_val = self.hazardsvc.get_earthquake_hazard_value(hazard_dataset_id, hazard_demand_type,
                                                                            demand_units, location.y, location.x)
                    demand_type = local_fragility_set['demandType']
                elif hazard_type == 'tornado':
                    demand_type = local_fragility_set['demandType']
                    demand_units = local_fragility_set['demandUnits']
                    hazard_val = self.hazardsvc.get_tornado_hazard_value(hazard_dataset_id, demand_units, location.y,
                                                                         location.x, 0)
                elif hazard_type == 'hurricane':
                    # TODO implement hurricane
                    demand_type = local_fragility_set['demandType']
                    print("hurricane not yet implemented")
                elif hazard_type == 'tsunami':
                    hazard_demand_type = BuildingUtil.get_hazard_demand_type(building, local_fragility_set, hazard_type)

                    demand_units = local_fragility_set["demandUnits"]
                    point = str(location.y) + "," + str(location.x)
                    hazard_val = self.hazardsvc.get_tsunami_hazard_values(hazard_dataset_id,
                                                                          hazard_demand_type,
                                                                          demand_units,
                                                                          [point])[0]["hazardValue"]

                    # Sometimes the geotiffs give large negative values for out of bounds instead of 0
                    if hazard_val <= 0.0:
                        if BuildingUtil.DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY in fragility_set:
                            local_fragility_set = fragility_set[BuildingUtil.DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY]
                            hazard_demand_type = BuildingUtil.get_hazard_demand_type(building, local_fragility_set,
                                                                                     hazard_type)
                            demand_units = local_fragility_set["demandUnits"]
                            hazard_val = self.hazardsvc.get_tsunami_hazard_values(hazard_dataset_id,
                                                                                  hazard_demand_type,
                                                                                  demand_units,
                                                                                  [point])[0]["hazardValue"]
                            if hazard_val <= 0.0:
                                hazard_val = 0.0
                            else:
                                demand_type = hazard_demand_type

                    else:
                        demand_type = hazard_demand_type

                dmg_probability = AnalysisUtil.calculate_damage_json(local_fragility_set, hazard_val)
            else:
                dmg_probability['immocc'] = 0.0
                dmg_probability['lifesfty'] = 0.0
                dmg_probability['collprev'] = 0.0

            dmg_interval = AnalysisUtil.calculate_damage_interval(dmg_probability)
            mean_damage = AnalysisUtil.calculate_mean_damage(dmg_ratio_tbl, dmg_interval)
            mean_damage_dev = AnalysisUtil.calculate_mean_damage_std_deviation(dmg_ratio_tbl, dmg_interval,
                                                                               mean_damage['meandamage'])

            bldg_results['guid'] = building['properties']['guid']
            bldg_results.update(dmg_probability)
            bldg_results.update(dmg_interval)
            bldg_results.update(mean_damage)
            bldg_results.update(mean_damage_dev)

            bldg_results['hazardtype'] = demand_type
            bldg_results['hazardval'] = hazard_val

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
                    'type': ['ergo:buildingInventoryVer4', 'ergo:buildingInventoryVer5'],
                },
                {
                    'id': 'dmg_ratios',
                    'required': True,
                    'description': 'Bridge Damage Ratios',
                    'type': ['ergo:buildingDamageRatios'],
                },

            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'bridges',
                    'description': 'CSV file of building structural damage',
                    'type': 'ergo:buildingDamageVer4'
                }
            ]
        }
