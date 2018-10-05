import collections
import concurrent.futures
from pyincore import BaseAnalysis, HazardService, FragilityService
from pyincore import AnalysisUtil, GeoUtil
# from itertools import repeat
import fiona
import os


class BridgeDamage(BaseAnalysis):

    def __init__(self, incoreClient):
        print("called bridge damage init")
        self.hazardsvc = HazardService(incoreClient)
        self.fragilitysvc = FragilityService(incoreClient)

        super(BridgeDamage, self).__init__(incoreClient)

    def run(self):
        print('Running the bridge damage analysis')

        # Setup fragility and hazard services
        inventory = InventoryDataset("/home/cnavarro/git/pyincore/cache_data/nbsrbridges")

        # This should work, but doesn't
        # bridge_set = self.get_input_dataset("bridges").get_inventory_reader()
        bridge_set = inventory.inventory_set

        print("num cpu in run is")
        print(self.get_parameter("num_cpu"))

        results = []
        user_defined_cpu = 1

        if not self.get_parameter("num_cpu") is None and self.get_parameter("num_cpu") > 0:
            print("num cpu specified")
            user_defined_cpu = self.get_parameter("num_cpu")
        else:
            print("use default num cpu")

        parallelism = AnalysisUtil.determine_parallelism_locally(self, len(bridge_set), user_defined_cpu)

        avg_bulk_input_size = int(len(bridge_set) / parallelism)
        inventory_args = []
        count = 0
        inventory_list = list(bridge_set)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.bridge_damage_concurrent_future(self.bridge_damage_analysis_bulk_input, parallelism,
                                                       inventory_args)

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))

        print("Finished running bridge damage")
        return True

    def bridge_damage_concurrent_future(self, function_name, parallelism, *args):
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=parallelism) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def bridge_damage_analysis_bulk_input(self, bridges):
        result = []
        fragility_sets = self.fragilitysvc.map_fragilities(self.get_parameter("mapping_id"), bridges, "Non-Retrofit Fragility ID Code")
        for bridge in bridges:
            fragility_set = None
            if bridge["id"] in fragility_sets:
                fragility_set = fragility_sets[bridge["id"]]

            result.append(self.bridge_damage_analysis(bridge, fragility_set))

        return result

    def bridge_damage_analysis(self, bridge, fragility_set):
        bridge_results = collections.OrderedDict()

        hazard_val = 0.0
        hazard_type = ""
        exceedence_probability = [0.0, 0.0, 0.0, 0.0]
        dmg_intervals = [0.0, 0.0, 0.0, 0.0, 0.0]
        mean_damage = 0.0;
        expected_damage = "None"
        retrofit_type = "Non-Retrofit"
        retrofit_cost = 0.0

        if fragility_set is not None:
            location = GeoUtil.get_location(bridge)
            # Start here, need to add the hazard dataset id to the analysis parameter list
            # hazard_val = self.hazardsvc.get_earthquake_hazard_value(self.hazard_dataset_id,
            #                                                         fragility_set['demandType'].lower(),
            #                                                         fragility_set['demandUnits'],
            #                                                         location.y, location.x)


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
        bridge_results["hazardtype"] = hazard_type
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
                    'type': 'bridge-damage'
                }
            ]
        }


class InventoryDataset:
    def __init__(self, filename):
        self.inventory_set = None
        if os.path.isdir(filename):
            layers = fiona.listlayers(filename)
            if len(layers) > 0:
                # for now, open a first shapefile
                print("reading from this reader 1")
                self.inventory_set = fiona.open(filename, layer = layers[0])
        else:
            print("reading from this reader 2")
            self.inventory_set = fiona.open(filename)

    def close(self):
        self.inventory_set.close()

    def __del__(self):
        self.close()

# class BridgeDamage:
#     def __init__(self, client, dmg_ratio_dir: str, hazard_service: str, output_file_name: str):
#
#         self.client = client
#
#         # Create hazard and fragility service
#         self.hazardsvc = HazardService(self.client)
#
#         # Find hazard type and id
#         hazard_service_split = hazard_service.split("/")
#         self.hazard_type = hazard_service_split[0] if hazard_service_split is not None else "Unknown"
#         self.hazard_dataset_id = hazard_service_split[1]
#
#         self.fragilitysvc = FragilityService(self.client)
#         self.fragility_key = BridgeUtil.DEFAULT_FRAGILITY_KEY
#         dmg_ratio = None
#         if (os.path.isfile(dmg_ratio_dir)):
#             dmg_ratio = DamageRatioDataset(dmg_ratio_dir)
#         else:
#             for file in os.listdir(dmg_ratio_dir):
#                 if file.endswith(".csv"):
#                     dmg_ratio = DamageRatioDataset(os.path.abspath(os.path.join(dmg_ratio_dir, file)))
#
#         self.dmg_ratios = dmg_ratio.damage_ratio
#         # damage weights for buildings
#         self.dmg_weights = [
#             float(self.dmg_ratios[1]['Best Mean Damage Ratio']),
#             float(self.dmg_ratios[2]['Best Mean Damage Ratio']),
#             float(self.dmg_ratios[3]['Best Mean Damage Ratio']),
#             float(self.dmg_ratios[4]['Best Mean Damage Ratio']),
#             float(self.dmg_ratios[5]['Best Mean Damage Ratio']),
#             float(self.dmg_ratios[6]['Best Mean Damage Ratio'])]
#         self.output_file_name = output_file_name

    # @staticmethod
    # def get_output_metadata():
    #     output = {"dataType": "ergo:bridgeDamage", "format": "table"}
    #     return output
    #
    # def get_damage(self, inventory_set: dict, mapping_id: str, use_liquefaction: bool, use_hazard_uncertainty: bool):
    #     """
    #     Main function to perform bridge damage analysis.
    #
    #     :return: a list of ordered dictionary.
    #     """
    #     output = []
    #
    #     fragility_set = self.fragilitysvc.map_fragilities(mapping_id, inventory_set, self.fragility_key)
    #     if len(fragility_set) > 0:
    #         for item in inventory_set:
    #             if item["id"] in fragility_set:
    #                 output.append(self.bridge_damage_analysis(item, fragility_set[item['id']], use_liquefaction,
    #                                                           use_hazard_uncertainty))
    #                 BridgeUtil.write_to_file(output,
    #                                          ["guid", "ls-slight", "ls-moderat", "ls-extensi", "ls-complet", "none",
    #                                           "slight-mod", "mod-extens", "ext-comple", "complete", "meandamage",
    #                                           "expectval", "retrofit", "retro_cost", "hazardtype", "hazardval"],
    #                                          self.output_file_name)
    #
    #     return output
    #
    # def bridge_damage_analysis(self, cur_bridge, cur_fragility, use_liquefaction, use_hazard_uncertainty):
    #     """
    #     Calculates bridge damage results for single fragility.
    #
    #     :param cur_bridge: current bridge
    #     :param cur_fragility: current fragility
    #     :return: an ordered dictionary with 15 fields listed below
    #     """
    #     bridge_results = collections.OrderedDict()
    #
    #     center_point = GeoUtil.get_location(cur_bridge)
    #     hazard_val = self.hazardsvc.get_earthquake_hazard_value(self.hazard_dataset_id,
    #                                                             cur_fragility['demandType'].lower(),
    #                                                             cur_fragility['demandUnits'],
    #                                                             center_point.y, center_point.x)
    #     hazard_type = cur_fragility['demandType']
    #     hazard_std_dev = BridgeUtil.get_hazard_std_dev() if use_hazard_uncertainty else 0.0
    #     exceedence_probability = BridgeUtil.get_probability_of_exceedence(cur_fragility, hazard_val, hazard_std_dev,
    #                                                                       use_liquefaction)
    #     dmg_intervals = BridgeUtil.get_damage_state_intervals(exceedence_probability)
    #     mean_damage = BridgeUtil.get_mean_damage(dmg_intervals, 1, cur_bridge, self.dmg_weights)
    #     expected_damage = BridgeUtil.get_expected_damage(mean_damage, self.dmg_ratios)
    #     retrofit_cost = BridgeUtil.get_retrofit_cost(self.fragility_key)
    #     retrofit_type = BridgeUtil.get_retrofit_type(self.fragility_key)
    #
    #     bridge_results["guid"] = cur_bridge['properties']['guid']
    #     bridge_results["ls-slight"] = exceedence_probability[0]
    #     bridge_results["ls-moderat"] = exceedence_probability[1]
    #     bridge_results["ls-extensi"] = exceedence_probability[2]
    #     bridge_results["ls-complet"] = exceedence_probability[3]
    #     bridge_results["none"] = dmg_intervals[0]
    #     bridge_results["slight-mod"] = dmg_intervals[1]
    #     bridge_results["mod-extens"] = dmg_intervals[2]
    #     bridge_results["ext-comple"] = dmg_intervals[3]
    #     bridge_results["complete"] = dmg_intervals[4]
    #     bridge_results["meandamage"] = mean_damage
    #     bridge_results["expectval"] = expected_damage
    #     bridge_results["retrofit"] = retrofit_type
    #     bridge_results["retro_cost"] = retrofit_cost
    #     bridge_results["hazardtype"] = hazard_type
    #     bridge_results["hazardval"] = hazard_val
    #
    #     return bridge_results
