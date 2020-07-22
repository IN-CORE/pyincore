# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""Road Damage Analysis by Hurricane Inundation

"""

import collections
import os
import concurrent.futures
import pandas as pd
from itertools import repeat

from pyincore import BaseAnalysis, HazardService, FragilityService, \
    AnalysisUtil, GeoUtil


class RoadFailure(BaseAnalysis):
    """Computes road damage by hurricane inundation.

    Args:
        incore_client: Service client with authentication info

    """

    DEFAULT_EQ_FRAGILITY_KEY = "inundationDuration"

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(RoadFailure, self).__init__(incore_client)

    def run(self):
        """Execute road damage analysis """
        # road dataset
        road_dataset = self.get_input_dataset("roads").get_inventory_reader()

        # distance to shore table data frame
        distance_df = self.get_input_dataset("distance_table").get_dataframe_from_csv()

        # set distance field name in the table
        distance_field_name = self.get_parameter("distance_field_name")

        # Get hazard type
        hazard_type = self.get_parameter("hazard_type")

        # Get hazard input
        hazard_dataset_id = self.get_parameter("hazard_id")
        user_defined_cpu = 1

        if not self.get_parameter("num_cpu") is None and self.get_parameter(
                "num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        dataset_size = len(road_dataset)
        num_workers = AnalysisUtil.determine_parallelism_locally(self,
                                                                 dataset_size,
                                                                 user_defined_cpu)

        avg_bulk_input_size = int(dataset_size / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(road_dataset)
        while count < len(inventory_list):
            inventory_args.append(
                inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.road_damage_concurrent_future(self.road_damage_analysis_bulk_input, num_workers,
                                                     inventory_args, repeat(distance_df),
                                                     repeat(distance_field_name), repeat(hazard_type),
                                                     repeat(hazard_dataset_id))

        self.set_result_csv_data("result", results,
                                 name=self.get_parameter("result_name"))

        return True

    def road_damage_concurrent_future(self, function_name, num_workers,
                                      *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Maximum number workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with road damage values and other data/metadata.

        """
        output = []
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=num_workers) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def road_damage_analysis_bulk_input(self, roads, distance_df, distance_field_name, hazard_type,
                                        hazard_dataset_id):
        """Run road damage analysis by hurricane inundation.

        Args:
            roads (list): multiple roads from road dataset.
            distance_df (object): data frame for distance to shore table
            distance_field_name (str): field name representing the distance to shore
            hazard_type (str): Hazard type
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with failure probability of road and other data/metadata.

        """
        result = []

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = self.DEFAULT_EQ_FRAGILITY_KEY
            self.set_parameter("fragility_key", fragility_key)

        # get fragility set
        fragility_sets = self.fragilitysvc.match_inventory(
            self.get_input_dataset("dfr3_mapping_set"), roads, fragility_key)

        for road in roads:
            if road["id"] in fragility_sets.keys():
                # find out distance value
                distance = float(distance_df.loc[distance_df['guid']
                                                 == road['properties']["guid"]][distance_field_name])

                result.append(self.road_damage_analysis(road, distance, hazard_type,
                                                        fragility_sets[road["id"]],
                                                        hazard_dataset_id))

        return result

    def road_damage_analysis(self, road, distance, hazard_type, fragility_set, hazard_dataset_id):
        """Run road damage for a single road segment.

        Args:
            road (obj): a single road feature.
            distance (float): distance to shore from the road
            hazard_type (str): hazard type.
            fragility_set (obj): A JSON description of fragility assigned to the road.
            hazard_dataset_id (str): A hazard dataset to use.

        Returns:
            OrderedDict: A dictionary with probability of failure values and other data/metadata.
        """

        road_results = collections.OrderedDict()

        if fragility_set is not None:
            demand_type = fragility_set.demand_type.lower()
            demand_units = fragility_set.demand_units
            location = GeoUtil.get_location(road)
            point = str(location.y) + "," + str(location.x)

            if hazard_type == 'hurricane':
                hazard_resp = self.hazardsvc.get_hurricane_values(hazard_dataset_id,
                                                                  "inundationDuration", demand_units, [point])
            else:
                raise ValueError(
                    "Hazard type are not currently supported.")

            dur_q = hazard_resp[0]['hazardValue']

            if dur_q <= 0.0:
                dur_q = 0.0

            fragility_vars = {'x': dur_q, 'y': distance}
            fragility_curve = fragility_set.fragility_curves[0]
            pf = fragility_curve.compute_custom_limit_state_probability(fragility_vars)

            road_results['guid'] = road['properties']['guid']
            road_results['failprob'] = pf
            road_results['demandtype'] = demand_type
            road_results['hazardtype'] = hazard_type
            road_results['hazardval'] = dur_q

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
                    'id': 'distance_field_name',
                    'required': True,
                    'description': 'field name representing the distance in the table',
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
                    'id': 'num_cpu',
                    'required': False,
                    'description': 'If using parallel execution, the number of cpus to request',
                    'type': int
                }
            ],
            'input_datasets': [
                {
                    'id': 'roads',
                    'required': True,
                    'description': 'Road Inventory',
                    'type': ['ergo:roadLinkTopo', 'ergo:roads'],
                },
                {
                    'id': 'distance_table',
                    'required': True,
                    'description': 'Distance to Shore Table',
                    'type': ['incore:distanceToShore'],
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
                    'type': 'incore:roadFailure'
                }
            ]
        }
