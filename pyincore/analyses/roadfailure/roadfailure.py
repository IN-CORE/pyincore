# Copyright (c) 2020 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""Road Damage Analysis by Hurricane Inundation

"""

import collections
import concurrent.futures
from itertools import repeat

from pyincore import BaseAnalysis, HazardService, FragilityService, \
    AnalysisUtil, GeoUtil


class RoadFailure(BaseAnalysis):
    """Computes road damage by hurricane inundation.

    Args:
        incore_client: Service client with authentication info

    """

    DEFAULT_HURRICANE_FRAGILITY_KEY = "inundationDuration"

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

        # TODO this has to be changed when semantic service lanuched based on it
        # set distance field name in the table
        distance_field_name = "distance"

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

        (results, hazard_results) = self.road_damage_concurrent_future(
            self.road_damage_analysis_bulk_input, num_workers,
            inventory_args,
            repeat(distance_df), repeat(distance_field_name),
            repeat(hazard_type), repeat(hazard_dataset_id))

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))
        self.set_result_json_data("metadata",
                                  hazard_results,
                                  name=self.get_parameter("result_name") + "_additional_info")
        return True

    def road_damage_concurrent_future(self, function_name, num_workers,
                                      *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Maximum number workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            dict: An ordered dictionaries with road failure values.
            dict: An ordered dictionaries with other road data/metadata.

        """
        output_ds = []
        output_dmg = []
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=num_workers) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

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
            dict: An ordered dictionaries with road failure values.
            dict: An ordered dictionaries with other road data/metadata.

        """
        failure_results = []
        hazard_results = []

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = self.DEFAULT_HURRICANE_FRAGILITY_KEY
            self.set_parameter("fragility_key", fragility_key)

        # get fragility set
        fragility_sets = self.fragilitysvc.match_inventory(
            self.get_input_dataset("dfr3_mapping_set"), roads, fragility_key)

        for road in roads:
            fragility_set = None
            distance = 0.0
            if road["id"] in fragility_sets.keys():
                fragility_set = fragility_sets[road["id"]]

                # find out distance value
                distance = float(distance_df.loc[distance_df['guid']
                                                 == road['properties']["guid"]][distance_field_name])

            (failure_result, hazard_result) = self.road_damage_analysis(road, distance, hazard_type,
                                                                            fragility_set, hazard_dataset_id)
            failure_results.append(failure_result)
            hazard_results.append(hazard_result)

        return failure_results, hazard_results

    def road_damage_analysis(self, road, distance, hazard_type, fragility_set, hazard_dataset_id):
        """Run road damage for a single road segment.

        Args:
            road (obj): A single road feature.
            distance (float): Distance to shore from the road.
            hazard_type (str): Hazard type (e.g. hurricane).
            fragility_set (obj): A JSON description of fragility assigned to the road.
            hazard_dataset_id (str): A hazard dataset to use.

        Returns:
            dict: An ordered dictionaries with road failure values.
            dict: An ordered dictionaries with other road data/metadata.

        """
        dur_q = 0.0
        demand_type = None
        demand_unit = None
        fragility_id = None
        failure_results = collections.OrderedDict()
        hazard_results = collections.OrderedDict()

        if fragility_set is not None:
            fragility_id = fragility_set.id
            demand_type = fragility_set.demand_types[0].lower()
            demand_unit = fragility_set.demand_units[0]
            location = GeoUtil.get_location(road)
            point = str(location.y) + "," + str(location.x)

            if hazard_type == 'hurricane':
                hazard_resp = self.hazardsvc.get_hurricane_values(hazard_dataset_id,
                                                                  "inundationDuration", demand_unit, [point])
            else:
                raise ValueError(
                    "Hazard type are not currently supported.")

            dur_q = hazard_resp[0]['hazardValue']
            if dur_q <= 0.0:
                dur_q = 0.0

            fragility_vars = {'x': dur_q, 'y': distance}
            pf = fragility_set.calculate_custom_limit_state(fragility_vars)

            failure_results['guid'] = road['properties']['guid']
            failure_results['failprob'] = pf['failure']

        hazard_results['guid'] = road['properties']['guid']
        hazard_results['hazardtype'] = hazard_type
        hazard_results['fragility_id'] = fragility_id
        hazard_results['demandtypes'] = demand_type
        hazard_results['demandunits'] = demand_unit
        hazard_results['hazardval'] = dur_q

        return failure_results, hazard_results

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
                    'description': 'CSV file of damage states for road failure',
                    'type': 'incore:roadFailureVer2'
                },
                {
                    'id': 'metadata',
                    'parent_type': 'roads',
                    'description': 'Json file with information about applied hazard value and fragility',
                    'type': 'incore:roadFailureSupplement'
                }
            ]
        }
