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


class BridgeDamage(BaseAnalysis):
    """Computes bridge structural damage for an earthquake hazard.

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

        results = self.bridge_damage_concurrent_future(
            self.bridge_damage_analysis_bulk_input, num_workers,
            inventory_args, repeat(hazard_type),
            repeat(hazard_dataset_id))

        self.set_result_csv_data("result", results,
                                 name=self.get_parameter("result_name"))

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
        output = []
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=num_workers) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def bridge_damage_analysis_bulk_input(self, bridges, hazard_type,
                                          hazard_dataset_id):
        """Run analysis for multiple bridges.

        Args:
            bridges (list): Multiple bridges from input inventory set.
            hazard_type (str): Hazard type, either earthquake, tornadoes, tsunami, or hurricane
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

        fragility_set = dict()
        fragility_set = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"),
                                                                 bridges, fragility_key)

        bridge_results = []
        list_bridges = bridges

        # Converting list of bridges into a dictionary for ease of reference
        bridges = dict()
        for br in list_bridges:
            bridges[br["id"]] = br
        list_bridges = None  # Clear as it's not needed anymore

        processed_bridges = []
        grouped_bridges = AnalysisUtil.group_by_demand_type(bridges, fragility_set)

        for demand, grouped_brs in grouped_bridges.items():

            input_demand_type = demand[0]
            input_demand_units = demand[1]

            # For every group of unique demand and demand unit, call the end-point once
            br_chunks = list(AnalysisUtil.chunks(grouped_brs, 50))  # TODO: Move to globals?
            for brs in br_chunks:
                points = []
                for br_id in brs:
                    location = GeoUtil.get_location(bridges[br_id])
                    points.append(str(location.y) + "," + str(location.x))

                if hazard_type == "earthquake":
                    hazard_vals = \
                        self.hazardsvc.get_earthquake_hazard_values(
                            hazard_dataset_id,
                            input_demand_type,
                            input_demand_units,
                            points)
                elif hazard_type == "tsunami":
                    hazard_vals = self.hazardsvc.get_tsunami_hazard_values(
                        hazard_dataset_id, input_demand_type, input_demand_units, points)
                elif hazard_type == "tornado":
                    hazard_vals = self.hazardsvc.get_tornado_hazard_values(
                        hazard_dataset_id, input_demand_units, points)
                elif hazard_type == "hurricane":
                    hazard_vals = self.hazardsvc.get_hurricanewf_values(
                        hazard_dataset_id, input_demand_type, input_demand_units, points)
                else:
                    raise ValueError("We only support Earthquake, Tornado, Tsunami, and Hurricane at the moment!")

                # Parse the batch hazard value results and map them back to the building and fragility.
                # This is a potential pitfall as we are relying on the order of the returned results
                i = 0
                for br_id in brs:
                    bridge_result = collections.OrderedDict()
                    bridge = bridges[br_id]
                    selected_fragility_set = fragility_set[br_id]

                    hazard_val = hazard_vals[i]['hazardValue']

                    hazard_std_dev = 0.0
                    if use_hazard_uncertainty:
                        # TODO Get this from API once implemented
                        raise ValueError("Uncertainty Not Implemented!")

                    adjusted_fragility_set = copy.deepcopy(selected_fragility_set)
                    if use_liquefaction and 'liq' in bridge['properties']:
                        for fragility in adjusted_fragility_set.fragility_curves:
                            fragility.adjust_fragility_for_liquefaction(bridge['properties']['liq'])

                    dmg_probability = adjusted_fragility_set.calculate_limit_state(hazard_val, std_dev=hazard_std_dev)
                    retrofit_cost = BridgeUtil.get_retrofit_cost(fragility_key)
                    retrofit_type = BridgeUtil.get_retrofit_type(fragility_key)

                    dmg_intervals = AnalysisUtil.calculate_damage_interval(dmg_probability)

                    bridge_result['guid'] = bridge['properties']['guid']
                    bridge_result.update(dmg_probability)
                    bridge_result.update(dmg_intervals)
                    bridge_result["retrofit"] = retrofit_type
                    bridge_result["retrocost"] = retrofit_cost
                    bridge_result["demandtype"] = input_demand_type
                    bridge_result["demandunits"] = input_demand_units
                    bridge_result["hazardtype"] = hazard_type
                    bridge_result["hazardval"] = hazard_val

                    # add spans to bridge output so mean damage calculation can use that info
                    if "spans" in bridge["properties"] and bridge["properties"]["spans"] \
                            is not None and bridge["properties"]["spans"].isdigit():
                        bridge_result['spans'] = int(bridge["properties"]["spans"])
                    elif "SPANS" in bridge["properties"] and bridge["properties"]["SPANS"] \
                            is not None and bridge["properties"]["SPANS"].isdigit():
                        bridge_result['spans'] = int(bridge["properties"]["SPANS"])
                    else:
                        bridge_result['spans'] = 1

                    bridge_results.append(bridge_result)
                    processed_bridges.append(br_id)  # remove processed bridges
                    i = i + 1

        unmapped_dmg_probability = {"ls-slight": 0.0, "ls-moderat": 0.0,
                                    "ls-extensi": 0.0, "ls-complet": 0.0}
        unmapped_dmg_intervals = AnalysisUtil.calculate_damage_interval(unmapped_dmg_probability)
        for br_id, br in bridges.items():
            if br_id not in processed_bridges:
                unmapped_br_result = collections.OrderedDict()
                unmapped_br_result['guid'] = br['properties']['guid']
                unmapped_br_result.update(unmapped_dmg_probability)
                unmapped_br_result.update(unmapped_dmg_intervals)
                unmapped_br_result["retrofit"] = "Non-Retrofit"
                unmapped_br_result["retrocost"] = 0.0
                unmapped_br_result["demandtype"] = "None"
                unmapped_br_result['demandunits'] = "None"
                unmapped_br_result["hazardtype"] = "None"
                unmapped_br_result['hazardval'] = 0.0
                bridge_results.append(unmapped_br_result)

        return bridge_results

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
                    'type': ['ergo:bridges'],
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
                    'type': 'ergo:bridgeDamage'
                }
            ]
        }
