# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import collections
import concurrent.futures
from itertools import repeat
import copy

from pyincore import AnalysisUtil, GeoUtil
from pyincore import BaseAnalysis, HazardService, FragilityService
from pyincore.analyses.bridgedamage.bridgeutil import BridgeUtil
from pyincore.models.dfr3curve import DFR3Curve


class BridgeDamage(BaseAnalysis):
    """Computes bridge structural damage for earthquake, tsunami, tornado, and hurricane hazards.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(BridgeDamage, self).__init__(incore_client)

    def run(self):
        """Executes bridge damage analysis."""
        # Bridge dataset
        bridge_set = self.get_input_dataset("bridges").get_inventory_reader()

        # Get hazard input
        hazard_type = self.get_parameter("hazard_type")
        hazard_dataset_id = self.get_parameter("hazard_id")
        user_defined_cpu = 1

        if not self.get_parameter("num_cpu") is None and self.get_parameter(
                "num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self, len(
            bridge_set), user_defined_cpu)

        avg_bulk_input_size = int(len(bridge_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(bridge_set)
        while count < len(inventory_list):
            inventory_args.append(
                inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        (ds_results, damage_results) = self.bridge_damage_concurrent_future(
            self.bridge_damage_analysis_bulk_input, num_workers,
            inventory_args, repeat(hazard_type),
            repeat(hazard_dataset_id))

        self.set_result_csv_data("result", ds_results, name=self.get_parameter("result_name"))
        self.set_result_json_data("metadata",
                                  damage_results,
                                  name=self.get_parameter("result_name") + "_additional_info")

        return True

    def bridge_damage_concurrent_future(self, function_name, num_workers,
                                        *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Maximum number workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with bridge damage values and other data/metadata.

        """
        output_ds = []
        output_dmg = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

    def bridge_damage_analysis_bulk_input(self, bridges, hazard_type,
                                          hazard_dataset_id):
        """Run analysis for multiple bridges.

        Args:
            bridges (list): Multiple bridges from input inventory set.
            hazard_type (str): Hazard type, either earthquake, tornado, tsunami, or hurricane.
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with bridge damage values and other data/metadata.

        """
        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = BridgeUtil.DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY if hazard_type == 'tsunami' else \
                BridgeUtil.DEFAULT_FRAGILITY_KEY
            self.set_parameter("fragility_key", fragility_key)

        # Hazard Uncertainty
        use_hazard_uncertainty = False
        if hazard_type == "earthquake" and self.get_parameter(
                "use_hazard_uncertainty") is not None:
            use_hazard_uncertainty = self.get_parameter(
                "use_hazard_uncertainty")

        # Liquefaction
        use_liquefaction = False
        if hazard_type == "earthquake" and self.get_parameter(
                "use_liquefaction") is not None:
            use_liquefaction = self.get_parameter("use_liquefaction")

        fragility_set = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), bridges,
                                                          fragility_key)

        values_payload = []
        unmapped_bridges = []
        mapped_bridges = []
        for b in bridges:
            bridge_id = b["id"]
            if bridge_id in fragility_set:
                location = GeoUtil.get_location(b)
                loc = str(location.y) + "," + str(location.x)

                demands = fragility_set[bridge_id].demand_types
                units = fragility_set[bridge_id].demand_units
                value = {
                    "demands": demands,
                    "units": units,
                    "loc": loc
                }
                values_payload.append(value)
                mapped_bridges.append(b)

            else:
                unmapped_bridges.append(b)

        # not needed anymore as they are already split into mapped and unmapped
        del bridges

        if hazard_type == 'earthquake':
            hazard_vals = self.hazardsvc.post_earthquake_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'tornado':
            hazard_vals = self.hazardsvc.post_tornado_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'tsunami':
            hazard_vals = self.hazardsvc.post_tsunami_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'hurricane':
            hazard_vals = self.hazardsvc.post_hurricane_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'flood':
            hazard_vals = self.hazardsvc.post_flood_hazard_values(hazard_dataset_id, values_payload)
        else:
            raise ValueError("The provided hazard type is not supported yet by this analysis")

        ds_results = []
        damage_results = []

        i = 0
        for bridge in mapped_bridges:
            ds_result = dict()
            damage_result = dict()
            dmg_probability = dict()
            dmg_intervals = dict()
            selected_fragility_set = fragility_set[bridge["id"]]

            if isinstance(selected_fragility_set.fragility_curves[0], DFR3Curve):
                # Supports multiple demand types in same fragility
                hazard_val = AnalysisUtil.update_precision_of_lists(hazard_vals[i]["hazardValues"])
                input_demand_types = hazard_vals[i]["demands"]
                input_demand_units = hazard_vals[i]["units"]

                hval_dict = dict()
                j = 0
                for d in selected_fragility_set.demand_types:
                    hval_dict[d] = hazard_val[j]
                    j += 1

                if not AnalysisUtil.do_hazard_values_have_errors(hazard_vals[i]["hazardValues"]):
                    bridge_args = selected_fragility_set.construct_expression_args_from_inventory(bridge)
                    dmg_probability = \
                        selected_fragility_set.calculate_limit_state(hval_dict,
                                                                     inventory_type="bridge",
                                                                     **bridge_args)
                    dmg_intervals = selected_fragility_set.calculate_damage_interval(dmg_probability,
                                                                                     hazard_type=hazard_type,
                                                                                     inventory_type="bridge")
            else:
                raise ValueError("One of the fragilities is in deprecated format. This should not happen. If you are "
                                 "seeing this please report the issue.")

            retrofit_cost = BridgeUtil.get_retrofit_cost(fragility_key)
            retrofit_type = BridgeUtil.get_retrofit_type(fragility_key)

            ds_result['guid'] = bridge['properties']['guid']
            ds_result.update(dmg_probability)
            ds_result.update(dmg_intervals)
            ds_result['haz_expose'] = AnalysisUtil.get_exposure_from_hazard_values(hazard_val, hazard_type)

            damage_result['guid'] = bridge['properties']['guid']
            damage_result['fragility_id'] = selected_fragility_set.id
            damage_result["retrofit"] = retrofit_type
            damage_result["retrocost"] = retrofit_cost
            damage_result["demandtypes"] = input_demand_types
            damage_result["demandunits"] = input_demand_units
            damage_result["hazardtype"] = hazard_type
            damage_result["hazardval"] = hazard_val

            # add spans to bridge output so mean damage calculation can use that info
            if "spans" in bridge["properties"] and bridge["properties"]["spans"] is not None:
                if isinstance(bridge["properties"]["spans"], str) and bridge["properties"]["spans"].isdigit():
                    damage_result['spans'] = int(bridge["properties"]["spans"])
                elif isinstance(bridge["properties"]["spans"], int):
                    damage_result['spans'] = bridge["properties"]["spans"]
            elif "SPANS" in bridge["properties"] and bridge["properties"]["SPANS"] is not None:
                if isinstance(bridge["properties"]["SPANS"], str) and bridge["properties"]["SPANS"].isdigit():
                    damage_result['SPANS'] = int(bridge["properties"]["SPANS"])
                elif isinstance(bridge["properties"]["SPANS"], int):
                    damage_result['SPANS'] = bridge["properties"]["SPANS"]
            else:
                damage_result['spans'] = 1

            ds_results.append(ds_result)
            damage_results.append(damage_result)
            i += 1

        for bridge in unmapped_bridges:
            ds_result = dict()
            damage_result = dict()

            ds_result['guid'] = bridge['properties']['guid']

            damage_result['guid'] = bridge['properties']['guid']
            damage_result["retrofit"] = None
            damage_result["retrocost"] = None
            damage_result["demandtypes"] = None
            damage_result['demandunits'] = None
            damage_result["hazardtype"] = None
            damage_result['hazardval'] = None
            damage_result['spans'] = None

            ds_results.append(ds_result)
            damage_results.append(damage_result)

        return ds_results, damage_results

    def get_spec(self):
        """Get specifications of the bridge damage analysis.

        Returns:
            obj: A JSON object of specifications of the bridge damage analysis.

        """
        return {
            'name': 'bridge-damage',
            'description': 'bridge damage analysis',
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
            ],
            'input_datasets': [
                {
                    'id': 'bridges',
                    'required': True,
                    'description': 'Bridge Inventory',
                    'type': ['ergo:bridges', 'ergo:bridgesVer2', 'ergo:bridgesVer3'],
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
                    'parent_type': 'bridges',
                    'description': 'CSV file of bridge structural damage',
                    'type': 'ergo:bridgeDamageVer3'
                },
                {
                    'id': 'metadata',
                    'parent_type': 'bridges',
                    'description': 'additional metadata in json file about applied hazard value and '
                                   'fragility',
                    'type': 'incore:bridgeDamageSupplement'
                }
            ]
        }
