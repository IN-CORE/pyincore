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

class RoadDamage(BaseAnalysis):
    """Road Damage Analysis calculates the probability of road damage based on
    hazard type such as earthquake by calling fragility
    and hazard services.

    Args:
        incore_client (IncoreClient): Service authentication.

    """
    DEFAULT_FRAGILITY_KEY = "Non-Retrofit Fragility ID Code"

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(RoadDamage, self).__init__(incore_client)

    def run(self):
        """Executes road damage analysis."""
        # Road dataset
        road_set = self.get_input_dataset("roads").get_inventory_reader()

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = self.DEFAULT_FRAGILITY_KEY

        # Get hazard input
        hazard_dataset_id = self.get_parameter("hazard_id")

        # Get hazard type
        hazard_type = self.get_parameter("hazard_type")

        # Liquefaction
        use_liquefaction = False
        if self.get_parameter("use_liquefaction") is not None:
            use_liquefaction = self.get_parameter("use_liquefaction")

        # Get geology dataset for liquefaction
        geology_dataset_id = None
        if self.get_parameter("liquefaction_geology_dataset_id") is not None:
            geology_dataset_id = self.get_parameter("liquefaction_geology_dataset_id")

        user_defined_cpu = 1
        if self.get_parameter("num_cpu") is not None and self.get_parameter("num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self, len(road_set), user_defined_cpu)

        avg_bulk_input_size = int(len(road_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(road_set)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.road_damage_concurrent_future(self.road_damage_analysis_bulk_input, num_workers, inventory_args,
                                                     repeat(hazard_type), repeat(hazard_dataset_id),
                                                     repeat(geology_dataset_id), repeat(fragility_key),
                                                     repeat(use_liquefaction))

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

    def road_damage_analysis_bulk_input(self, roads, hazard_type, hazard_dataset_id, geology_dataset_id,
                                        fragility_key, use_liquefaction):
        """Run analysis for multiple roads.

        Args:
            roads (list): Multiple roads from input inventory set.
            hazard_type (str): A hazard type of the hazard exposure.
            hazard_dataset_id (str): An id of the hazard exposure.
            geology_dataset_id (str): An id of the geology for use in liquefaction.
            fragility_key (str): Fragility key describing the type of fragility.
            use_liquefaction (bool): Liquefaction. True for using liquefaction information to modify the damage,
                False otherwise.

        Returns:
            list: A list of ordered dictionaries with road damage values and other data/metadata.

        """

        result = []
        mapping = self.get_input_dfr3_mapping_set()
        fragility_sets = self.fragilitysvc.match_inventory(mapping, roads, fragility_key)

        for road in roads:
            if road["id"] in fragility_sets.keys():
                result.append(self.road_damage_analysis(road, fragility_sets[road["id"]],
                                                        hazard_dataset_id, hazard_type,
                                                        geology_dataset_id, use_liquefaction))

        return result

    def road_damage_analysis(self, road, fragility_set, hazard_dataset_id,
                             hazard_type, geology_dataset_id, use_liquefaction):
        """Calculates road damage results for a single section of road.

        Args:
            road (obj): A JSON mapping of a geometric object from the inventory: current road section.
            fragility_set (obj): A JSON description of fragility assigned to the road.
            hazard_dataset_id (str): A hazard dataset to use.
            hazard_type (str): A hazard type of the hazard exposure.
            geology_dataset_id (str): An id of the geology for use in liquefaction.
            use_liquefaction (bool): Liquefaction. True for using liquefaction information to modify the damage,
                False otherwise.

        Returns:
            OrderedDict: A dictionary with road damage values and other data/metadata.

        """

        try:
            road_results = collections.OrderedDict()

            demand_type = "None"
            dmg_probability = {"ls-slight": 0.0, "ls-moderat": 0.0,
                               "ls-extensi": 0.0, "ls-complet": 0.0}

            road_results['guid'] = road['properties']['guid']

            if fragility_set is not None:
                location = GeoUtil.get_location(road)
                demand_type = fragility_set.demand_type
                demand_units = fragility_set.demand_units
                if hazard_type == 'earthquake':
                    if demand_type.lower() == 'pgd' and use_liquefaction and geology_dataset_id is not None:
                        location_str = str(location.y) + "," + str(location.x)
                        liquefaction = self.hazardsvc.get_liquefaction_values(hazard_dataset_id, geology_dataset_id,
                                                                              demand_units, [location_str])
                        if demand_type in liquefaction[0]:
                            liquefaction_val = liquefaction[0][demand_type]
                        elif demand_type.lower() in liquefaction[0]:
                            liquefaction_val = liquefaction[0][demand_type.lower()]
                        elif demand_type.upper() in liquefaction[0]:
                            liquefaction_val = liquefaction[0][demand_type.upper]
                        else:
                            liquefaction_val = 0.0
                        road_results['hazardval'] = liquefaction_val
                    else:
                        road_results['hazardval'] = self.hazardsvc.get_earthquake_hazard_value(hazard_dataset_id,
                                                                                               demand_type,
                                                                                               demand_units, location.y,
                                                                                               location.x)
                elif hazard_type == 'tsunami':
                    road_results['hazardval'] = self.hazardsvc.get_tsunami_hazard_value(hazard_dataset_id,demand_type,
                                                                                        demand_units, location.y,
                                                                                        location.x)
                    if road_results['hazardval'] < 0:
                        road_results['hazardval'] = 0
                else:
                    raise ValueError("Earthquake and tsunamis are the only hazards supported for road damage")
                dmg_probability = fragility_set.calculate_limit_state(road_results['hazardval'])

            dmg_interval = AnalysisUtil.calculate_damage_interval(dmg_probability)

            road_results.update(dmg_probability)
            road_results.update(dmg_interval)
            road_results['demandtype'] = demand_type

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
            'input_dfr3_mapping_set': {
                'required': True,
                'description': "input dfr3 mapping set"
            },
            'input_datasets': [
                {
                    'id': 'roads',
                    'required': True,
                    'description': 'Road Inventory',
                    'type': ['ergo:roadLinkTopo','incore:roads']
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
