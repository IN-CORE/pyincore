# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import collections
import concurrent.futures
import traceback
from itertools import repeat

from pyincore import BaseAnalysis, HazardService, FragilityService, AnalysisUtil, GeoUtil
from pyincore.analyses.roaddamage.roadutil import RoadUtil


class RoadDamage(BaseAnalysis):
    """Road Damage Analysis calculates the probability of road damage based on
    hazard type such as earthquake by calling fragility
    and hazard services.

    Args:
        incore_client (IncoreClient): Service authentication.

    """
    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(RoadDamage, self).__init__(incore_client)

    def run(self):
        """Executes road damage analysis."""
        # Road dataset
        road_set = self.get_input_dataset("roads").get_inventory_reader()

        dmg_ratio_csv = self.get_input_dataset("dmg_ratios").get_csv_reader()
        dmg_ratio_tbl = AnalysisUtil.get_csv_table_rows(dmg_ratio_csv)

        # Get hazard input
        hazard_dataset_id = self.get_parameter("hazard_id")

        # Hazard type of the exposure
        hazard_type = self.get_parameter("hazard_type")

        # Hazard Uncertainty
        use_hazard_uncertainty = False
        if self.get_parameter("use_hazard_uncertainty") is not None:
            use_hazard_uncertainty = self.get_parameter("use_hazard_uncertainty")

        # Liquefaction
        use_liquefaction = False
        if self.get_parameter("use_liquefaction") is not None:
            use_liquefaction = self.get_parameter("use_liquefaction")

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = RoadUtil.DEFAULT_FRAGILITY_KEY

        user_defined_cpu = 1

        if not self.get_parameter("num_cpu") is None and self.get_parameter("num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self, len(road_set), user_defined_cpu)

        avg_bulk_input_size = int(len(road_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(road_set)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.road_damage_concurrent_future(self.road_damage_analysis_bulk_input, num_workers,
                                                         inventory_args, repeat(hazard_type), repeat(hazard_dataset_id),
                                                         repeat(dmg_ratio_tbl), repeat(fragility_key),
                                                         repeat(use_hazard_uncertainty), repeat(use_liquefaction))

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))

        return True

    def road_damage_concurrent_future(self, function_name, parallelism, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            parallelism (int): Number of workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with road damage values and other data/metadata.

        """
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=parallelism) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def road_damage_analysis_bulk_input(self, roads, hazard_type, hazard_dataset_id, dmg_ratio_tbl, fragility_key,
                                        use_hazard_uncertainty, use_liquefaction):
        """Run analysis for multiple roads.

        Args:
            roads (list): Multiple roads from input inventory set.
            hazard_type (str): A hazard type of the hazard exposure.
            hazard_dataset_id (str): An id of the hazard exposure.
            dmg_ratio_tbl (obj): A damage ratio table, including weights to compute mean damage.
            fragility_key (str): Fragility key describing the type of fragility.
            use_hazard_uncertainty (bool):  Hazard uncertainty. True for using uncertainty when computing damage,
                False otherwise.
            use_liquefaction (bool): Liquefaction. True for using liquefaction information to modify the damage,
                False otherwise.

        Returns:
            list: A list of ordered dictionaries with road damage values and other data/metadata.

        """
        result = []
        fragility_key = self.get_parameter("fragility_key")

        fragility_sets = dict()
        fragility_sets[fragility_key] = self.fragilitysvc.map_fragilities(self.get_parameter("mapping_id"), roads,
                                                                          fragility_key)

        for road in roads:
            fragility_set = dict()
            if road["id"] in fragility_sets[fragility_key]:
                fragility_set[fragility_key] = fragility_sets[fragility_key][road["id"]]

            result.append(self.road_damage_analysis(road, dmg_ratio_tbl, fragility_set, hazard_dataset_id,
                                                        hazard_type, use_hazard_uncertainty, use_liquefaction))

        return result

    def road_damage_analysis(self, road, dmg_ratio_tbl, fragility_set, hazard_dataset_id, hazard_type,
                             use_hazard_uncertainty, use_liquefaction):
        """Calculates road damage results for a single section of road.

        Args:
            road (obj): A JSON mapping of a geometric object from the inventory: current road section.
            dmg_ratio_tbl (obj): A table of damage ratios for mean damage.
            fragility_set (obj): A JSON description of fragility assigned to the road.
            hazard_dataset_id (str): A hazard dataset to use.
            hazard_type (str): A hazard type of the hazard exposure.

        Returns:
            OrderedDict: A dictionary with road damage values and other data/metadata.

        """
        try:
            road_results = collections.OrderedDict()

            hazard_val = 0.0
            demand_type = "None"

            dmg_probability = collections.OrderedDict()
            dmg_interval = collections.OrderedDict()
            mean_damage = collections.OrderedDict()
            mean_damage['meandamage'] = 0.0
            mean_damage_dev = collections.OrderedDict()
            mean_damage_dev['mdamagedev'] = 0.0
            hazard_std_dev = 0.0

            if bool(fragility_set):
                location = GeoUtil.get_location(road)
                fragility_key = self.get_parameter("fragility_key")
                local_fragility_set = fragility_set[fragility_key]
                if hazard_type == 'earthquake':
                    # TODO include liquefaction and hazard uncertainty
                    demand_units = local_fragility_set['demandUnits']
                    #hazard_demand_type = local_fragility_set['demandType']
                    # Hardcoded to PGA currently, need to update
                    hazard_demand_type = "PGA"
                    hazard_val = self.hazardsvc.get_earthquake_hazard_value(hazard_dataset_id, hazard_demand_type,
                                                                            demand_units, location.y, location.x)
                    # Hardcoding this to see if the error is my analysis or the hazard value
                    #hazard_val = 126.38
                    demand_type = local_fragility_set['demandType']
                else:
                    print("Earthquake is the only hazard supported for road damage")

                dmg_probability = RoadUtil.get_probability_of_damage(road, local_fragility_set, hazard_val,
                                                                     hazard_std_dev ,use_liquefaction)
            else:
                dmg_probability['immocc'] = 0.0
                dmg_probability['lifesfty'] = 0.0
                dmg_probability['collprev'] = 0.0

            dmg_interval = AnalysisUtil.calculate_damage_interval(dmg_probability)
            mean_damage = AnalysisUtil.calculate_mean_damage(dmg_ratio_tbl, dmg_interval)
            mean_damage_dev = AnalysisUtil.calculate_mean_damage_std_deviation(dmg_ratio_tbl, dmg_interval,
                                                                               mean_damage['meandamage'])

            road_results['guid'] = road['properties']['guid']
            road_results.update(dmg_probability)
            road_results.update(dmg_interval)
            road_results.update(mean_damage)
            road_results.update(mean_damage_dev)

            road_results['hazardtype'] = demand_type
            road_results['hazardval'] = hazard_val

            return road_results

        except Exception as e:
            # This prints the type, value and stacktrace of error being handled.
            traceback.print_exc()
            print()
            raise e

    def get_spec(self):
        """Get specifications of the road damage analysis.

        Returns:
            obj: A JSON object of specifications of the road damage analysis.

        """
        return {
            'name': 'road-damage',
            'description': 'road damage analysis',
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
                    'id': 'liquefaction_geology_dataset_id',
                    'required': False,
                    'description': 'Liquefaction geology/susceptibility dataset id. '
                                   'If not provided, liquefaction will be ignored',
                    'type': str
                },
                {
                    'id': 'liquefaction_fragility_key',
                    'required': False,
                    'description': 'Fragility key to use in liquefaction mapping dataset',
                    'type': str
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
                    'id': 'roads',
                    'required': True,
                    'description': 'Road Inventory',
                    'type': 'ergo:roadLinkTopo'
                },
                {
                    'id': 'dmg_ratios',
                    'required': True,
                    'description': 'Road Damage Ratios',
                    'type': ['ergo:roadDamageRatios'],
                },

            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'roads',
                    'description': 'CSV file of road structural damage',
                    'type': 'ergo:roadDamage'
                }
            ]
        }
