"""pyincore.analyses.bridgedamage.bridgedamage

Copyright (c) 2017 University of Illinois and others.  All rights reserved.
This program and the accompanying materials are made available under the
terms of the BSD-3-Clause which accompanies this distribution,
and is available at https://opensource.org/licenses/BSD-3-Clause

"""
import collections
import concurrent.futures
from pyincore import BaseAnalysis, HazardService, FragilityService
from pyincore import AnalysisUtil, GeoUtil
from pyincore.analyses.bridgedamage.bridgeutil import BridgeUtil
from itertools import repeat


class BridgeDamage(BaseAnalysis):
    """Computes bridge structural damage for an earthquake hazard

    """

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(BridgeDamage, self).__init__(incore_client)

    def run(self):
        """
        Executes bridge damage analysis
        """

        # Bridge dataset
        bridge_set = self.get_input_dataset("bridges").get_inventory_reader()

        dmg_ratio_csv = self.get_input_dataset("dmg_ratios").get_csv_reader()
        dmg_ratio_tbl = BridgeUtil.get_damage_ratio_rows(dmg_ratio_csv)

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = BridgeUtil.DEFAULT_FRAGILITY_KEY

        # Get hazard input
        hazard_dataset_id = self.get_parameter("hazard_id")

        # Hazard type, note this is here for future use if additional hazards are supported by this analysis
        hazard_type = self.get_parameter("hazard_type")

        # Hazard Uncertainty
        use_hazard_uncertainty = False
        if self.get_parameter("use_hazard_uncertainty") is not None:
            use_hazard_uncertainty = self.get_parameter("use_hazard_uncertainty")

        # Liquefaction
        use_liquefaction = False
        if self.get_parameter("use_liquefaction") is not None:
            use_liquefaction = self.get_parameter("use_liquefaction")

        results = []
        user_defined_cpu = 1

        if not self.get_parameter("num_cpu") is None and self.get_parameter("num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self, len(bridge_set), user_defined_cpu)

        avg_bulk_input_size = int(len(bridge_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(bridge_set)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.bridge_damage_concurrent_future(self.bridge_damage_analysis_bulk_input, num_workers,
                                                       inventory_args, repeat(hazard_dataset_id), repeat(dmg_ratio_tbl),
                                                       repeat(fragility_key), repeat(use_hazard_uncertainty),
                                                       repeat(use_liquefaction))

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))

        return True

    def bridge_damage_concurrent_future(self, function_name, num_workers, *args):
        """
        Utilizes concurrent.future module

        :param function_name: the function to be parallelized
        :param num_workers: number of max workers in parallelization
        :param args: all the arguments in order to pass into parameter function_name
        :return: output: list of OrderedDict
        """
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def bridge_damage_analysis_bulk_input(self, bridges, hazard_dataset_id, dmg_ratio_tbl, fragility_key,
                                          use_hazard_uncertainty, use_liquefaction):
        """
        Run analysis for multiple bridges

        :param bridges: multiple buildings from input inventory set
        :param hazard_dataset_id: id of the hazard exposure
        :param dmg_ratio_tbl: damage ratios table
        :param fragility_key: fragility key to use for mapping bridges to fragilities
        :param use_hazard_uncertainty: use hazard uncertainty when computing damage
        :param use_liquefaction: if bridge contains liquefaction information use it to modify the damage
        :return: results: a list of OrderedDict
        """
        result = []
        fragility_sets = self.fragilitysvc.map_fragilities(self.get_parameter("mapping_id"), bridges, fragility_key)
        for bridge in bridges:
            fragility_set = None
            if bridge["id"] in fragility_sets:
                fragility_set = fragility_sets[bridge["id"]]

            result.append(self.bridge_damage_analysis(bridge, fragility_set, hazard_dataset_id, dmg_ratio_tbl,
                                                      fragility_key, use_hazard_uncertainty, use_liquefaction))

        return result

    def bridge_damage_analysis(self, bridge, fragility_set, hazard_dataset_id, dmg_ratio_tbl, fragility_key,
                               use_hazard_uncertainty, use_liquefaction):
        """
        Calculates bridge damage results for a single bridge.

        :param bridge: current bridge
        :param fragility_set: fragility assigned to the bridge
        :param hazard_dataset_id: hazard dataset to use
        :param dmg_ratio_tbl: table of damage ratios for mean damage
        :param fragility_key: fragility key to use for mapping bridges to fragilities
        :param use_hazard_uncertainty: include hazard uncertainty in damage analysis
        :param use_liquefaction: use liquefaction data, if available to modify damage

        :return: an ordered dictionary with bridge damage and other data/metadata
        """
        bridge_results = collections.OrderedDict()

<<<<<<< HEAD
        center_point = GeoUtil.get_location(cur_bridge)
        hazard_val_set = self.hazardsvc.get_earthquake_hazard_values(self.hazard_dataset_id,
                                                                cur_fragility['demandType'].lower(),
                                                                cur_fragility['demandUnits'],
                                                                points=[center_point.y, center_point.x])
        hazard_val = hazard_val_set[0]['hazardValue']

        hazard_type = cur_fragility['demandType']
        hazard_std_dev = BridgeUtil.get_hazard_std_dev() if use_hazard_uncertainty else 0.0
        exceedence_probability = BridgeUtil.get_probability_of_exceedence(cur_fragility, hazard_val, hazard_std_dev,
                                                                          use_liquefaction)
        dmg_intervals = BridgeUtil.get_damage_state_intervals(exceedence_probability)
        mean_damage = BridgeUtil.get_mean_damage(dmg_intervals, 1, cur_bridge, self.dmg_weights)
        expected_damage = BridgeUtil.get_expected_damage(mean_damage, self.dmg_ratios)
        retrofit_cost = BridgeUtil.get_retrofit_cost(self.fragility_key)
        retrofit_type = BridgeUtil.get_retrofit_type(self.fragility_key)

        bridge_results["guid"] = cur_bridge['properties']['guid']
=======
        hazard_val = 0.0
        demand_type = "Unknown"
        exceedence_probability = [0.0, 0.0, 0.0, 0.0]
        dmg_intervals = [0.0, 0.0, 0.0, 0.0, 0.0]
        mean_damage = 0.0
        expected_damage = "Unknown"
        retrofit_type = "Non-Retrofit"
        retrofit_cost = 0.0

        if fragility_set is not None:
            location = GeoUtil.get_location(bridge)
            demand_type = fragility_set['demandType']
            demand_units = fragility_set['demandUnits']
            # Start here, need to add the hazard dataset id to the analysis parameter list
            hazard_resp = self.hazardsvc.get_earthquake_hazard_values(hazard_dataset_id, demand_type, demand_units,
                                                                     [location.y, location.x])
            hazard_val = hazard_resp[0]['hazardValue']
            hazard_std_dev = 0.0

            # if use_hazard_uncertainty:
            # TODO this value needs to come from the hazard service
            # hazard_std_dev = ...

            exceedence_probability = BridgeUtil.get_probability_of_exceedence(bridge, fragility_set, hazard_val,
                                                                              hazard_std_dev, use_liquefaction)

            dmg_intervals = BridgeUtil.get_damage_state_intervals(exceedence_probability)
            mean_damage = BridgeUtil.get_mean_damage(dmg_intervals, 1, bridge, dmg_ratio_tbl)
            expected_damage = BridgeUtil.get_expected_damage(mean_damage, dmg_ratio_tbl)
            retrofit_cost = BridgeUtil.get_retrofit_cost(fragility_key)
            retrofit_type = BridgeUtil.get_retrofit_type(fragility_key)

        bridge_results['guid'] = bridge['properties']['guid']
>>>>>>> a759cc33a2f5d39a572bcd43dd29d88018b72ac7
        bridge_results["ls-slight"] = exceedence_probability[0]
        bridge_results["ls-moderat"] = exceedence_probability[1]
        bridge_results["ls-extensi"] = exceedence_probability[2]
        bridge_results["ls-complet"] = exceedence_probability[3]
        bridge_results["none"] = dmg_intervals[0]
        bridge_results["slight-mod"] = dmg_intervals[1]
        bridge_results["mod-extens"] = dmg_intervals[2]
        bridge_results["ext-comple"] = dmg_intervals[3]
        bridge_results["complete"] = dmg_intervals[4]
        bridge_results["meandamage"] = mean_damage
        bridge_results["expectval"] = expected_damage
        bridge_results["retrofit"] = retrofit_type
        bridge_results["retro_cost"] = retrofit_cost
        bridge_results["hazardtype"] = demand_type
        bridge_results["hazardval"] = hazard_val

        return bridge_results

<<<<<<< HEAD
=======
    def get_spec(self):
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
                },
                {
                    'id': 'dmg_ratios',
                    'required': True,
                    'description': 'Bridge Damage Ratios',
                    'type': ['ergo:bridgeDamageRatios'],
                },

            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'bridges',
                    'type': 'bridge-damage'
                }
            ]
        }
>>>>>>> a759cc33a2f5d39a572bcd43dd29d88018b72ac7
