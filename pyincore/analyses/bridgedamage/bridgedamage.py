import collections
import concurrent.futures
from pyincore import BaseAnalysis, HazardService, FragilityService
from pyincore import AnalysisUtil, GeoUtil
from pyincore.analyses.bridgedamage.bridgeutil import BridgeUtil
from itertools import repeat


class BridgeDamage(BaseAnalysis):

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
        dmg_ratio_rows = BridgeUtil.get_damage_ratio_rows(dmg_ratio_csv)
        mean_dmg_weights = BridgeUtil.get_damage_ratio_values(dmg_ratio_rows, 'Best Mean Damage Ratio')

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = BridgeUtil.DEFAULT_FRAGILITY_KEY

        # Get hazard input
        hazard_dataset_id = self.get_parameter("hazard_id")

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
                                                       inventory_args, repeat(hazard_dataset_id),
                                                       repeat(use_hazard_uncertainty), repeat(use_liquefaction),
                                                       repeat(dmg_ratio_rows), repeat(mean_dmg_weights),
                                                       repeat(fragility_key))

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))

        print("Finished running bridge damage")
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

    def bridge_damage_analysis_bulk_input(self, bridges, hazard_dataset_id, use_hazard_uncertainty, use_liquefaction,
                                          dmg_ratio_data, mean_dmg_weights, fragility_key):
        """
        Run analysis for multiple bridges

        :param bridges: multiple buildings from input inventory set
        :param hazard_dataset_id: id of the hazard exposure
        :param use_hazard_uncertainty: use hazard uncertainty when computing damage
        :param use_liquefaction: if bridge contains liquefaction information use it to modify the damage
        :param mean_dmg_weights: weights to compute mean damage
        :param dmg_ratio_data: row data for damage ratios table
        :param fragility_key: fragility key to use for mapping bridges to fragilities
        :return: results: a list of OrderedDict
        """
        result = []
        fragility_sets = self.fragilitysvc.map_fragilities(self.get_parameter("mapping_id"), bridges, fragility_key)
        for bridge in bridges:
            fragility_set = None
            if bridge["id"] in fragility_sets:
                fragility_set = fragility_sets[bridge["id"]]

            result.append(self.bridge_damage_analysis(bridge, fragility_set, hazard_dataset_id, use_hazard_uncertainty,
                                                      use_liquefaction, dmg_ratio_data, mean_dmg_weights, fragility_key))

        return result

    def bridge_damage_analysis(self, bridge, fragility_set, hazard_dataset_id, use_hazard_uncertainty, use_liquefaction,
                               dmg_ratio_data, mean_dmg_weights, fragility_key):
        """
        Calculates bridge damage results for a single bridge.

        :param bridge: current bridge
        :param fragility_set: fragility assigned to the bridge
        :return: an ordered dictionary with bridge damage and other data/metadata
        """
        bridge_results = collections.OrderedDict()

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
            mean_damage = BridgeUtil.get_mean_damage(dmg_intervals, 1, bridge, mean_dmg_weights)
            expected_damage = BridgeUtil.get_expected_damage(mean_damage, dmg_ratio_data)
            retrofit_cost = BridgeUtil.get_retrofit_cost(fragility_key)
            retrofit_type = BridgeUtil.get_retrofit_type(fragility_key)

        bridge_results['guid'] = bridge['properties']['guid']
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
