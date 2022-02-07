# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import collections
import concurrent.futures
from itertools import repeat

from pyincore import BaseAnalysis, HazardService, FragilityService, AnalysisUtil, GeoUtil
from pyincore.models.dfr3curve import DFR3Curve


class RoadDamage(BaseAnalysis):
    """Road Damage Analysis calculates the probability of road damage based on an earthquake or tsunami hazard.

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

        (ds_results, damage_results) = self.road_damage_concurrent_future(self.road_damage_analysis_bulk_input,
                                                                          num_workers,
                                                                          inventory_args,
                                                                          repeat(hazard_type),
                                                                          repeat(hazard_dataset_id),
                                                                          repeat(use_hazard_uncertainty),
                                                                          repeat(geology_dataset_id),
                                                                          repeat(fragility_key),
                                                                          repeat(use_liquefaction))

        self.set_result_csv_data("result", ds_results, name=self.get_parameter("result_name"))
        self.set_result_json_data("metadata",
                                  damage_results,
                                  name=self.get_parameter("result_name") + "_additional_info")

        return True

    def road_damage_concurrent_future(self, function_name, num_workers, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Number of workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            output_ds: A list of ordered dictionaries with road damage values
            output_dmg: A list of ordered dictionaries with other road data/metadata.

        """

        output_ds = []
        output_dmg = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

    def road_damage_analysis_bulk_input(self, roads, hazard_type, hazard_dataset_id, use_hazard_uncertainty,
                                        geology_dataset_id, fragility_key, use_liquefaction):
        """Run analysis for multiple roads.

        Args:
            roads (list): Multiple roads from input inventory set.
            hazard_type (str): A hazard type of the hazard exposure (earthquake or tsunami).
            hazard_dataset_id (str): An id of the hazard exposure.
            use_hazard_uncertainty(bool): Flag to indicate use uncertainty or not
            geology_dataset_id (str): An id of the geology for use in liquefaction.
            fragility_key (str): Fragility key describing the type of fragility.
            use_liquefaction (bool): Liquefaction. True for using liquefaction information to modify the damage,
                False otherwise.

        Returns:
            list: A list of ordered dictionaries with road damage values and other data/metadata.
            list: A list of ordered dictionaries with other road data/metadata.

        """
        fragility_sets = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), roads,
                                                           fragility_key)

        values_payload = []
        mapped_roads = []
        unmapped_roads = []
        pgd_flag = True  # for liquefaction
        liquefaction_resp = None

        for road in roads:
            if road["id"] in fragility_sets.keys():
                fragility_set = fragility_sets[road["id"]]
                location = GeoUtil.get_location(road)
                loc = str(location.y) + "," + str(location.x)
                demands = fragility_set.demand_types
                # for liquefaction
                if any(demand.lower() != 'pgd' for demand in demands):
                    pgd_flag = False
                units = fragility_set.demand_units
                value = {
                    "demands": demands,
                    "units": units,
                    "loc": loc
                }
                values_payload.append(value)
                mapped_roads.append(road)
            else:
                unmapped_roads.append(road)
        del roads

        # get hazard and liquefaction values
        if hazard_type == 'earthquake':
            hazard_resp = self.hazardsvc.post_earthquake_hazard_values(hazard_dataset_id, values_payload)

            if pgd_flag and use_liquefaction and geology_dataset_id is not None:
                liquefaction_resp = self.hazardsvc.post_liquefaction_values(hazard_dataset_id, geology_dataset_id,
                                                                            values_payload)

        elif hazard_type == 'tsunami':
            hazard_resp = self.hazardsvc.post_tsunami_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'hurricane':
            hazard_resp = self.hazardsvc.post_hurricane_hazard_values(hazard_dataset_id, values_payload)
        else:
            raise ValueError("The provided hazard type is not supported yet by this analysis")

        # calculate LS and DS
        ds_results = []
        damage_results = []
        for i, road in enumerate(mapped_roads):
            dmg_probability = dict()
            dmg_interval = dict()
            demand_types_liq = None
            demand_units_liq = None
            liq_hazard_vals = None
            liquefaction_prob = None
            selected_fragility_set = fragility_sets[road["id"]]
            hazard_std_dev = 0.0
            if use_hazard_uncertainty:
                raise ValueError("Uncertainty Not Implemented Yet.")

            if isinstance(selected_fragility_set.fragility_curves[0], DFR3Curve):
                hazard_vals = AnalysisUtil.update_precision_of_lists(hazard_resp[i]["hazardValues"])
                demand_types = hazard_resp[i]["demands"]
                demand_units = hazard_resp[i]["units"]
                hval_dict = dict()
                for j, d in enumerate(selected_fragility_set.demand_types):
                    hval_dict[d] = hazard_vals[j]

                if not AnalysisUtil.do_hazard_values_have_errors(hazard_resp[i]["hazardValues"]):
                    road_args = selected_fragility_set.construct_expression_args_from_inventory(road)
                    dmg_probability = selected_fragility_set.calculate_limit_state(
                        hval_dict, inventory_type='road', **road_args)

                    # if there is liquefaction, overwrite the hazardval with liquefaction value
                    # recalculate dmg_probability and dmg_interval
                    if liquefaction_resp is not None and len(liquefaction_resp) > 0:
                        liq_hazard_vals = AnalysisUtil.update_precision_of_lists(liquefaction_resp[i]["pgdValues"])
                        demand_types_liq = liquefaction_resp[i]['demands']
                        demand_units_liq = liquefaction_resp[i]['units']
                        liquefaction_prob = liquefaction_resp[i]['liqProbability']
                        liq_hval_dict = dict()
                        for j, d in enumerate(liquefaction_resp[i]["demands"]):
                            liq_hval_dict[d] = liq_hazard_vals[j]
                        dmg_probability = selected_fragility_set.calculate_limit_state(
                            liq_hval_dict,
                            inventory_type='road',
                            **road_args)

                    dmg_interval = selected_fragility_set.calculate_damage_interval(dmg_probability,
                                                                                    hazard_type=hazard_type,
                                                                                    inventory_type="road")
            else:
                raise ValueError("One of the fragilities is in deprecated format. This should not happen. If you are "
                                 "seeing this please report the issue.")

            ds_result = dict()
            ds_result['guid'] = road['properties']['guid']
            ds_result.update(dmg_probability)
            ds_result.update(dmg_interval)
            ds_result['haz_expose'] = AnalysisUtil.get_exposure_from_hazard_values(hazard_vals, hazard_type)

            damage_result = dict()
            damage_result['guid'] = road['properties']['guid']
            damage_result['fragility_id'] = selected_fragility_set.id
            damage_result['demandtypes'] = demand_types
            damage_result['demandunits'] = demand_units
            damage_result['hazardtype'] = hazard_type
            damage_result['hazardvals'] = hazard_vals
            damage_result['liqdemandtypes'] = demand_types_liq
            damage_result['liqdemandunits'] = demand_units_liq
            damage_result['liqhazvals'] = liq_hazard_vals
            damage_result['liqprobability'] = liquefaction_prob

            ds_results.append(ds_result)
            damage_results.append(damage_result)

        for road in unmapped_roads:
            ds_result = dict()
            damage_result = dict()

            ds_result['guid'] = road['properties']['guid']

            damage_result['guid'] = road['properties']['guid']
            damage_result['fragility_id'] = None
            damage_result['demandtypes'] = None
            damage_result['demandunits'] = None
            damage_result['hazardtype'] = None
            damage_result['hazardvals'] = None
            damage_result['liqdemandtypes'] = None
            damage_result['liqdemandunits'] = None
            damage_result['liqhazvals'] = None
            damage_result['liqprobability'] = None

            ds_results.append(ds_result)
            damage_results.append(damage_result)

        return ds_results, damage_results

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
                    'type': ['ergo:roadLinkTopo', 'incore:roads', 'ergo:roadLinkTopoVer2']
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
                    'type': 'ergo:roadDamageVer3'
                },
                {
                    'id': 'metadata',
                    'parent_type': 'roads',
                    'description': 'additional metadata in json file about applied hazard value and '
                                   'fragility',
                    'type': 'incore:roadDamageSupplement'
                }
            ]
        }
