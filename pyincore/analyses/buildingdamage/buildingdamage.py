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
from pyincore.models.dfr3curve import DFR3Curve


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

        # building retrofit strategy
        retrofit_strategy_dataset = self.get_input_dataset("retrofit_strategy")
        if retrofit_strategy_dataset is not None:
            retrofit_strategy = list(retrofit_strategy_dataset.get_csv_reader())
        else:
            retrofit_strategy = None

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

        (ds_results, damage_results) = self.building_damage_concurrent_future(self.building_damage_analysis_bulk_input,
                                                                              num_workers,
                                                                              inventory_args,
                                                                              repeat(retrofit_strategy),
                                                                              repeat(hazard_type),
                                                                              repeat(hazard_dataset_id))

        self.set_result_csv_data("ds_result", ds_results, name=self.get_parameter("result_name"))
        self.set_result_json_data("damage_result",
                                  damage_results,
                                  name=self.get_parameter("result_name") + "_additional_info")

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
        output_ds = []
        output_dmg = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=parallelism) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

    def building_damage_analysis_bulk_input(self, buildings, retrofit_strategy, hazard_type, hazard_dataset_id):
        """Run analysis for multiple buildings.

        Args:
            buildings (list): Multiple buildings from input inventory set.
            retrofit_strategy (list): building guid and its retrofit level 0, 1, 2, etc. This is Optional
            hazard_type (str): Hazard type, either earthquake, tornado, or tsunami.
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """

        fragility_key = self.get_parameter("fragility_key")
        fragility_sets = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), buildings,
                                                           fragility_key, retrofit_strategy)

        # Liquefaction
        use_liquefaction = False
        if hazard_type == "earthquake" and self.get_parameter("use_liquefaction") is not None:
            use_liquefaction = self.get_parameter("use_liquefaction")

        # Get geology dataset id containing liquefaction susceptibility
        geology_dataset_id = self.get_parameter("liquefaction_geology_dataset_id")

        values_payload = []
        values_payload_liq = []  # for liquefaction, if used
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

                if use_liquefaction and geology_dataset_id is not None:
                    value_liq = {
                        "demands": [""],
                        "units": [""],
                        "loc": loc
                    }
                    values_payload_liq.append(value_liq)
            else:
                unmapped_buildings.append(b)

        # not needed anymore as they are already split into mapped and unmapped
        del buildings

        if hazard_type == 'earthquake':
            hazard_vals = self.hazardsvc.post_earthquake_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'tornado':
            hazard_vals = self.hazardsvc.post_tornado_hazard_values(hazard_dataset_id, values_payload,
                                                                    self.get_parameter('seed'))
        elif hazard_type == 'tsunami':
            hazard_vals = self.hazardsvc.post_tsunami_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'hurricane':
            hazard_vals = self.hazardsvc.post_hurricane_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'flood':
            hazard_vals = self.hazardsvc.post_flood_hazard_values(hazard_dataset_id, values_payload)
        else:
            raise ValueError("The provided hazard type is not supported yet by this analysis")

        # Check if liquefaction is applicable
        if use_liquefaction and geology_dataset_id is not None:
            liquefaction_resp = self.hazardsvc.post_liquefaction_values(hazard_dataset_id, geology_dataset_id,
                                                                        values_payload_liq)

        ds_results = []
        damage_results = []

        i = 0
        for b in mapped_buildings:
            ds_result = dict()
            damage_result = dict()
            dmg_probability = dict()
            dmg_interval = dict()
            b_id = b["id"]
            selected_fragility_set = fragility_sets[b_id]

            # TODO: Once all fragilities are migrated to new format, we can remove this condition
            if isinstance(selected_fragility_set.fragility_curves[0], DFR3Curve):
                # Supports multiple demand types in same fragility
                b_haz_vals = AnalysisUtil.update_precision_of_lists(hazard_vals[i]["hazardValues"])
                b_demands = hazard_vals[i]["demands"]
                b_units = hazard_vals[i]["units"]

                hval_dict = dict()
                j = 0

                # To calculate damage, use demand type name from fragility that will be used in the expression, instead
                # of using what the hazard service returns. There could be a difference "SA" in DFR3 vs "1.07 SA"
                # from hazard
                for d in selected_fragility_set.demand_types:
                    hval_dict[d] = b_haz_vals[j]
                    j += 1
                if not AnalysisUtil.do_hazard_values_have_errors(hazard_vals[i]["hazardValues"]):
                    building_args = selected_fragility_set.construct_expression_args_from_inventory(b)

                    building_period = selected_fragility_set.fragility_curves[0].get_building_period(
                        selected_fragility_set.curve_parameters, **building_args)

                    dmg_probability = selected_fragility_set.calculate_limit_state(
                        hval_dict, **building_args, period=building_period)

                    if use_liquefaction and geology_dataset_id is not None and liquefaction_resp is not None:
                        ground_failure_prob = liquefaction_resp[i][BuildingUtil.GROUND_FAILURE_PROB]
                        dmg_probability = AnalysisUtil.update_precision_of_dicts(
                            AnalysisUtil.adjust_damage_for_liquefaction(dmg_probability, ground_failure_prob))

                    dmg_interval = selected_fragility_set.calculate_damage_interval(
                        dmg_probability, hazard_type=hazard_type, inventory_type="building")
            else:
                raise ValueError("One of the fragilities is in deprecated format. This should not happen. If you are "
                                 "seeing this please report the issue.")

            ds_result['guid'] = b['properties']['guid']
            damage_result['guid'] = b['properties']['guid']

            ds_result.update(dmg_probability)
            ds_result.update(dmg_interval)
            ds_result['haz_expose'] = AnalysisUtil.get_exposure_from_hazard_values(b_haz_vals, hazard_type)

            damage_result['fragility_id'] = selected_fragility_set.id
            damage_result['demandtype'] = b_demands
            damage_result['demandunits'] = b_units
            damage_result['hazardval'] = b_haz_vals

            if use_liquefaction and geology_dataset_id is not None:
                damage_result[BuildingUtil.GROUND_FAILURE_PROB] = ground_failure_prob

            ds_results.append(ds_result)
            damage_results.append(damage_result)
            i += 1

        for b in unmapped_buildings:
            ds_result = dict()
            damage_result = dict()
            ds_result['guid'] = b['properties']['guid']
            damage_result['guid'] = b['properties']['guid']
            damage_result['fragility_id'] = None
            damage_result['demandtype'] = None
            damage_result['demandunits'] = None
            damage_result['hazardval'] = None

            ds_results.append(ds_result)
            damage_results.append(damage_result)

        return ds_results, damage_results

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
                {
                    'id': 'seed',
                    'required': False,
                    'description': 'Initial seed for the tornado hazard value',
                    'type': int
                },
                {
                    'id': 'liquefaction_geology_dataset_id',
                    'required': False,
                    'description': 'Geology dataset id',
                    'type': str,
                }
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
                },
                {
                    'id': 'retrofit_strategy',
                    'required': False,
                    'description': 'Building retrofit strategy that contains guid and retrofit method',
                    'type': ['incore:retrofitStrategy']
                }
            ],
            'output_datasets': [
                {
                    'id': 'ds_result',
                    'parent_type': 'buildings',
                    'description': 'CSV file of damage states for building structural damage',
                    'type': 'ergo:buildingDamageVer6'
                },
                {
                    'id': 'damage_result',
                    'parent_type': 'buildings',
                    'description': 'Json file with information about applied hazard value and fragility',
                    'type': 'incore:buildingDamageSupplement'
                }
            ]
        }
