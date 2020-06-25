# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import collections
import concurrent.futures
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

        # Hazard Uncertainty
        use_hazard_uncertainty = False
        if self.get_parameter("use_hazard_uncertainty") is not None:
            use_hazard_uncertainty = self.get_parameter("use_hazard_uncertainty")

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

        results = self.road_damage_concurrent_future(self.road_damage_analysis_bulk_input, num_workers,
                                                     inventory_args,
                                                     repeat(hazard_type), repeat(hazard_dataset_id),
                                                     repeat(use_hazard_uncertainty),
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

    def road_damage_analysis_bulk_input(self, roads, hazard_type, hazard_dataset_id, use_hazard_uncertainty,
                                        geology_dataset_id, fragility_key, use_liquefaction):
        """Run analysis for multiple roads.

        Args:
            roads (list): Multiple roads from input inventory set.
            hazard_type (str): A hazard type of the hazard exposure.
            hazard_dataset_id (str): An id of the hazard exposure.
            use_hazard_uncertainty(bool): Flag to indicate use uncertainty or not
            geology_dataset_id (str): An id of the geology for use in liquefaction.
            fragility_key (str): Fragility key describing the type of fragility.
            use_liquefaction (bool): Liquefaction. True for using liquefaction information to modify the damage,
                False otherwise.

        Returns:
            list: A list of ordered dictionaries with road damage values and other data/metadata.

        """
        road_results = []
        fragility_sets = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), roads,
                                                           fragility_key)

        list_roads = roads

        # Converting list of roads into a dictionary for ease of reference
        roads = dict()
        for rd in list_roads:
            roads[rd["id"]] = rd
        del list_roads

        processed_roads = []
        grouped_roads = AnalysisUtil.group_by_demand_type(roads, fragility_sets)
        for demand, grouped_road_items in grouped_roads.items():
            input_demand_type = demand[0]
            input_demand_units = demand[1]

            # For every group of unique demand and demand unit, call the end-point once
            road_chunks = list(AnalysisUtil.chunks(grouped_road_items, 50))
            for road_chunk in road_chunks:
                points = []
                for road_id in road_chunk:
                    location = GeoUtil.get_location(roads[road_id])
                    points.append(str(location.y) + "," + str(location.x))

                liquefaction = []
                if hazard_type == 'earthquake':
                    hazard_vals = self.hazardsvc.get_earthquake_hazard_values(hazard_dataset_id, input_demand_type,
                                                                              input_demand_units,
                                                                              points)

                    if input_demand_type.lower() == 'pgd' and use_liquefaction and geology_dataset_id is not None:
                        liquefaction = self.hazardsvc.get_liquefaction_values(hazard_dataset_id, geology_dataset_id,
                                                                              input_demand_units, points)
                elif hazard_type == 'tornado':
                    raise ValueError('Earthquake and tsunamis are the only hazards supported for road damage')
                elif hazard_type == 'hurricane':
                    raise ValueError('Earthquake and tsunamis are the only hazards supported for road damage')
                elif hazard_type == 'tsunami':
                    hazard_vals = self.hazardsvc.get_tsunami_hazard_values(hazard_dataset_id, input_demand_type,
                                                                           input_demand_units, points)
                else:
                    raise ValueError("Missing hazard type.")

                # Parse the batch hazard value results and map them back to the building and fragility.
                # This is a potential pitfall as we are relying on the order of the returned results
                i = 0
                for road_id in road_chunk:
                    road_result = collections.OrderedDict()
                    road = roads[road_id]
                    hazard_val = hazard_vals[i]['hazardValue']

                    # Sometimes the geotiffs give large negative values for out of bounds instead of 0
                    if hazard_val <= 0.0:
                        hazard_val = 0.0

                    std_dev = 0.0
                    if use_hazard_uncertainty:
                        raise ValueError("Uncertainty Not Implemented Yet.")

                    selected_fragility_set = fragility_sets[road_id]
                    dmg_probability = selected_fragility_set.calculate_limit_state(hazard_val, std_dev=std_dev)
                    dmg_interval = AnalysisUtil.calculate_damage_interval(dmg_probability)

                    road_result['guid'] = road['properties']['guid']
                    road_result.update(dmg_probability)
                    road_result.update(dmg_interval)
                    road_result['demandtype'] = input_demand_type
                    road_result['demandunits'] = input_demand_units
                    road_result['hazardtype'] = hazard_type
                    road_result['hazardval'] = hazard_val

                    # if there is liquefaction, overwrite the hazardval with liquefaction value
                    # recalculate dmg_probability and dmg_interval
                    if len(liquefaction) > 0:
                        if input_demand_type in liquefaction[i]:
                            liquefaction_val = liquefaction[i][input_demand_type]
                        elif input_demand_type.lower() in liquefaction[i]:
                            liquefaction_val = liquefaction[i][input_demand_type.lower()]
                        elif input_demand_type.upper() in liquefaction[i]:
                            liquefaction_val = liquefaction[i][input_demand_type.upper]
                        else:
                            liquefaction_val = 0.0
                        dmg_probability = selected_fragility_set.calculate_limit_state(liquefaction_val,
                                                                                       std_dev=std_dev)
                        dmg_interval = AnalysisUtil.calculate_damage_interval(dmg_probability)

                        road_result['hazardval'] = liquefaction_val
                        road_result.update(dmg_probability)
                        road_result.update(dmg_interval)

                    road_results.append(road_result)
                    processed_roads.append(road_id)
                    i = i + 1

        unmapped_dmg_probability = {"ls-slight": 0.0, "ls-moderat": 0.0,
                                    "ls-extensi": 0.0, "ls-complet": 0.0}
        unmapped_dmg_intervals = AnalysisUtil.calculate_damage_interval(unmapped_dmg_probability)
        for road_id, rd in roads.items():
            if road_id not in processed_roads:
                unmapped_rd_result = collections.OrderedDict()
                unmapped_rd_result['guid'] = rd['properties']['guid']
                unmapped_rd_result.update(unmapped_dmg_probability)
                unmapped_rd_result.update(unmapped_dmg_intervals)
                unmapped_rd_result['demandtype'] = "None"
                unmapped_rd_result['demandunits'] = "None"
                unmapped_rd_result['hazardtype'] = "None"
                unmapped_rd_result['hazardval'] = 0.0
                road_results.append(unmapped_rd_result)

        return road_results

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
            'input_datasets': [
                {
                    'id': 'roads',
                    'required': True,
                    'description': 'Road Inventory',
                    'type': ['ergo:roadLinkTopo', 'incore:roads']
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
                    'parent_type': 'roads',
                    'description': 'CSV file of road structural damage',
                    'type': 'ergo:roadDamage'
                }
            ]
        }
