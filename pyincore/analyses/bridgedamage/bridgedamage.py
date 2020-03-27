# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import collections
import concurrent.futures
import random
from itertools import repeat

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
            fragility_key = BridgeUtil.DEFAULT_TSUNAMI_MMAX_FRAGILITY_KEY if hazard_type == 'tsunami' else \
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

        result = []
        fragility_sets = self.fragilitysvc.match_inventory(
            self.get_parameter("mapping_id"), bridges, fragility_key)
        for bridge in bridges:
            fragility_set = None
            if bridge["id"] in fragility_sets:
                fragility_set = fragility_sets[bridge["id"]]

            result.append(self.bridge_damage_analysis(bridge, fragility_set,
                                                      hazard_type,
                                                      hazard_dataset_id,
                                                      fragility_key,
                                                      use_hazard_uncertainty,
                                                      use_liquefaction))

        return result

    def bridge_damage_analysis(self, bridge, fragility_set, hazard_type,
                               hazard_dataset_id, fragility_key,
                               use_hazard_uncertainty, use_liquefaction):
        """Calculates bridge damage results for a single bridge.

        Args:
            bridge (obj): A JSON mapping of a geometric object from the inventory: current bridge.
            fragility_set (obj): A JSON description of fragility assigned to the bridge.
            hazard_type (str): Hazard type earthquake, tsunami, tornado and hurricane
            hazard_dataset_id (str): A hazard dataset to use.
            fragility_key (str): A fragility key to use for mapping bridges to fragilities.
            use_hazard_uncertainty (bool):  Hazard uncertainty. True for using uncertainty in damage analysis,
                False otherwise.
            use_liquefaction (bool): Liquefaction. True for using liquefaction information to modify the damage,
                False otherwise.

        Returns:
            OrderedDict: A dictionary with bridge damage values and other data/metadata.

        """
        bridge_results = collections.OrderedDict()

        hazard_val = 0.0
        demand_type = "Unknown"

        # default
        dmg_probability = {"ls-slight": 0.0, "ls-moderat": 0.0,
                           "ls-extensi": 0.0, "ls-complet": 0.0}
        retrofit_type = "Non-Retrofit"
        retrofit_cost = 0.0

        if fragility_set is not None:
            location = GeoUtil.get_location(bridge)
            demand_type = fragility_set['demandType']
            demand_units = fragility_set['demandUnits']
            point = str(location.y) + "," + str(location.x)

            if hazard_type == "earthquake":
                hazard_resp = \
                    self.hazardsvc.get_earthquake_hazard_values(
                        hazard_dataset_id,
                        demand_type,
                        demand_units,
                        [point])
            elif hazard_type == "tsunami":
                hazard_resp = self.hazardsvc.get_tsunami_hazard_values(
                    hazard_dataset_id, demand_type, demand_units, [point])
            elif hazard_type == "tornado":
                hazard_resp = self.hazardsvc.get_tornado_hazard_values(
                    hazard_dataset_id, demand_units, [point])
            elif hazard_type == "hurricane":
                hazard_resp = self.hazardsvc.get_hurricanewf_values(
                    hazard_dataset_id, demand_type, demand_units, [point])
            else:
                raise ValueError(
                    "We only support Earthquake, Tornado, Tsunami, and Hurricane at the moment!")

            hazard_val = hazard_resp[0]['hazardValue']
            hazard_std_dev = 0.0
            adjusted_fragility_set = fragility_set

            # TODO Get this from API once implemented
            if use_hazard_uncertainty:
                hazard_std_dev = random.random()

            if use_liquefaction and 'liq' in bridge['properties']:
                for fragility in adjusted_fragility_set["fragilityCurves"]:
                    AnalysisUtil.adjust_fragility_for_liquefaction(
                            fragility, bridge['properties']['liq'])

            dmg_probability = AnalysisUtil.calculate_limit_state(adjusted_fragility_set, hazard_val, std_dev=hazard_std_dev)
            retrofit_cost = BridgeUtil.get_retrofit_cost(fragility_key)
            retrofit_type = BridgeUtil.get_retrofit_type(fragility_key)

        dmg_intervals = AnalysisUtil.calculate_damage_interval(dmg_probability)

        bridge_results['guid'] = bridge['properties']['guid']
        bridge_results.update(dmg_probability)
        bridge_results.update(dmg_intervals)
        bridge_results["retrofit"] = retrofit_type
        bridge_results["retro_cost"] = retrofit_cost
        bridge_results["demand_type"] = demand_type
        bridge_results["hazardtype"] = hazard_type
        bridge_results["hazardval"] = hazard_val

        # add spans to bridge output so mean damage calculation can use that info
        if "spans" in bridge["properties"] and bridge["properties"]["spans"] \
                is not None and bridge["properties"]["spans"].isdigit():
            bridge_results['spans'] = int(bridge["properties"]["spans"])
        elif "SPANS" in bridge["properties"] and bridge["properties"]["SPANS"] \
                is not None and bridge["properties"]["SPANS"].isdigit():
            bridge_results['spans'] = int(bridge["properties"]["SPANS"])
        else:
            bridge_results['spans'] = 1

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
