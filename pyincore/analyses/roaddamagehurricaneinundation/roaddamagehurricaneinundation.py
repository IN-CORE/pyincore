# Copyright (c) 2019 University of Illinois and others. All rights reserved.
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


class RoadDamageHurricaneInundation(BaseAnalysis):
    """Computes road damage by hurricane inundation.

    Args:
        incore_client: Service client with authentication info

    """

    DEFAULT_EQ_FRAGILITY_KEY = "inundationDuration"

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(RoadDamageHurricaneInundation, self).__init__(incore_client)

    def run(self):
        """Execute road damage analysis """
        # road dataset
        road_dataset = self.get_input_dataset(
            "roads").get_inventory_reader()

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

        results = self.road_damage_concurrent_future(
            self.road_damage_analysis_bulk_input, num_workers,
            inventory_args, repeat(hazard_type), repeat(hazard_dataset_id))

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

    def road_damage_analysis_bulk_input(self, roads, hazard_type,
                                        hazard_dataset_id):
        """Run pipeline damage analysis for multiple pipelines.

        Args:
            roads (list): multiple roads from road dataset.
            hazard_type (str): Hazard type
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with pipeline damage values and other data/metadata.

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
                result.append(self.road_damage_analysis(road, hazard_type,
                                                        fragility_sets[road["id"]],
                                                        hazard_dataset_id))

        return result

    def road_damage_analysis(self, road, hazard_type, fragility_set, hazard_dataset_id):
        """Run pipeline damage for a single pipeline.

        Args:
            road (obj): a single pipeline.
            hazard_type (str): hazard type.
            fragility_set (obj): A JSON description of fragility assigned to the road.
            hazard_dataset_id (str): A hazard dataset to use.

        Returns:
            OrderedDict: A dictionary with pipeline damage values and other data/metadata.
        """

        road_results = collections.OrderedDict()
        pgv_repairs = 0.0
        pgd_repairs = 0.0
        liq_hazard_type = ""
        liq_hazard_val = 0.0
        liquefaction_prob = 0.0

        if fragility_set is not None:
            demand_type = fragility_set.demand_type.lower()
            demand_units = fragility_set.demand_units
            location = GeoUtil.get_location(road)
            point = str(location.y) + "," + str(location.x)

            # TODO this has to be implemented when hurricane endpoint get deveploed
            # if hazard_type == 'hurricane':
            #     hazard_resp = self.hazardsvc.get_hurricanewf_values(
            #         hazard_dataset_id, demand_type, demand_units, [point])
            # else:
            #     raise ValueError(
            #         "Hazard type are not currently supported.")

            # hazard_val = hazard_resp[0]['hazardValue']
            hazard_val = 1.5
            if hazard_val <= 0.0:
                hazard_val = 0.0

            # TODO dur_q should come from hazard service
            dur_q = 1
            distance = road['properties']['R__dist']
            fragility_vars = {'x': dur_q, 'y': distance}
            fragility_curve = fragility_set.fragility_curves[0]
            pf = fragility_curve.compute_custom_limit_state_probability(fragility_vars)

            road_results['guid'] = road['properties']['guid']
            road_results['failprob'] = pf
            road_results['demandtype'] = demand_type
            road_results['hazardtype'] = hazard_type
            road_results['hazardval'] = hazard_val

        return road_results

    def get_spec(self):
        """Get specifications of the pipeline damage analysis.

        Returns:
            obj: A JSON object of specifications of the pipeline damage analysis.

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
                    'type': 'ergo:roadDamage'
                }
            ]
        }
