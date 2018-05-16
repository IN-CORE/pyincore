#!/usr/bin/env python3

"""Building Damage Analysis

Usage:
    building_damage.py INVENTORY HAZARD MAPPING DMGRATIO BASEDATASETID EXECUTION
    building_damage.py INVENTORY HAZARD MAPPING DMGRATIO BASEDATASETID EXECUTION PARALLELISM

Options:
    INVENTORY     inventory file in ESRI shapefile
    HAZARD        type/id (e.g. earthquake/59f3315ec7d30d4d6741b0bb)
    MAPPING       fragility mapping id
    DMGRATIO      damage ratio file in CSV
    BASEDATASETID parent of the output file, needed for result ingestion
    EXECUTION     0 - process pool, 1 - thread pool, 2 - multiprocessing, other - sequential
    PARALLELISM   Number of concurrent threads/processes to use


"""
import collections
from pyincore import DamageRatioDataset, HazardService, FragilityService
from pyincore import GeoUtil, AnalysisUtil
from pyincore.analyses.buildingdamage.buildingutil import BuildingUtil
import os
import csv
import concurrent.futures
import traceback
from itertools import repeat


class BuildingDamage:
    def __init__(self, client, hazard_service: str, dmg_ratios: str):
        # TODO Should we move this outside of the building damage class?
        # Handle the case where Ergo data has an .mvz
        # In the case of multiple files, DataWolf creates a folder and passes that to the tool
        dmg_ratio = None
        if (os.path.isfile(dmg_ratios)):
            dmg_ratio = DamageRatioDataset(dmg_ratios)
        else:
            dmg_ratio_file = None
            for file in os.listdir(dmg_ratios):
                if file.endswith(".csv"):
                    dmg_ratio_file = os.path.join(dmg_ratios, file)
                    dmg_ratio = DamageRatioDataset(os.path.abspath(dmg_ratio_file))

        damage_ratios = dmg_ratio.damage_ratio

        # Find hazard type and id
        hazard_service_split = hazard_service.split("/")
        self.hazard_type = hazard_service_split[0]
        self.hazard_dataset_id = hazard_service_split[1]

        # Create Hazard and Fragility service
        self.hazardsvc = HazardService(client)
        self.fragilitysvc = FragilityService(client)

        # damage weights for buildings
        self.dmg_weights = [
            float(damage_ratios[1]['Mean Damage Factor']),
            float(damage_ratios[2]['Mean Damage Factor']),
            float(damage_ratios[3]['Mean Damage Factor']),
            float(damage_ratios[4]['Mean Damage Factor'])]
        self.dmg_weights_std_dev = [float(damage_ratios[1]['Deviation Damage Factor']),
                                    float(damage_ratios[2]['Deviation Damage Factor']),
                                    float(damage_ratios[3]['Deviation Damage Factor']),
                                    float(damage_ratios[4]['Deviation Damage Factor'])]

    @staticmethod
    def get_output_metadata():
        output = {}
        output["dataType"] = "ergo:buildingDamageVer4"
        output["format"] = "table"

        return output

    def get_damage(self, inventory_set: dict, mapping_id: str, base_dataset_id: str = None, num_threads: int = 0):
        output = []

        parallelism = AnalysisUtil.determine_parallelism_locally(self, len(inventory_set), num_threads)
        avg_bulk_input_size = int(len(inventory_set) / parallelism)
        inventory_args = []
        count = 0
        inventory_list = list(inventory_set)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        output = self.building_damage_concurrent_future(self.building_damage_analysis_bulky_input,
                                                        parallelism,
                                                        inventory_args,
                                                        repeat(mapping_id),
                                                        repeat(self.dmg_weights),
                                                        repeat(self.dmg_weights_std_dev),
                                                        repeat(self.hazardsvc),
                                                        repeat(self.hazard_dataset_id),
                                                        repeat(self.hazard_type))

        output_file_name = "dmg-results.csv"

        # Write Output to csv
        with open(output_file_name, 'w') as csv_file:
            # Write the parent ID at the top of the result data, if it is given
            if base_dataset_id is not None:
                csv_file.write(base_dataset_id + '\n')

            writer = csv.DictWriter(csv_file, dialect="unix",
                                    fieldnames=['guid', 'immocc', 'lifesfty', 'collprev', 'insignific', 'moderate',
                                                'heavy', 'complete', 'meandamage', 'mdamagedev', 'hazardtype',
                                                'hazardval'])
            writer.writeheader()
            writer.writerows(output)

        return output_file_name

    def building_damage_concurrent_future(self, function_name, parallelism, *args):
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=parallelism) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def building_damage_analysis_bulky_input(self, buildings, mapping_id, dmg_weights, dmg_weights_std_dev,
                                             hazardsvc, hazard_dataset_id, hazard_type):
        result = []
        fragility_sets = self.fragilitysvc.map_fragilities(mapping_id, buildings, "Non-Retrofit Fragility ID Code")

        for building in buildings:
            if building["id"] in fragility_sets.keys():
                result.append(self.building_damage_analysis(building, dmg_weights, dmg_weights_std_dev,
                                                            fragility_sets[building["id"]], hazardsvc,
                                                            hazard_dataset_id, hazard_type))

        return result

    def building_damage_analysis(self, building, dmg_weights, dmg_weights_std_dev, fragility_set, hazardsvc,
                                 hazard_dataset_id, hazard_type):
        try:
            bldg_results = collections.OrderedDict()

            hazard_val = 0.0
            demand_type = "Unknown"

            dmg_probability = collections.OrderedDict()

            # TODO what would be returned if no match found?
            if fragility_set is not None:

                hazard_demand_type = BuildingUtil.get_hazard_demand_type(building, fragility_set, hazard_type)
                demand_units = fragility_set['demandUnits']
                location = GeoUtil.get_location(building)

                # Update this once hazard service supports tornado
                if hazard_type == 'earthquake':
                    hazard_val = hazardsvc.get_earthquake_hazard_value(hazard_dataset_id, hazard_demand_type,
                                                                       demand_units, location.y,
                                                                       location.x)
                elif hazard_type == 'tornado':
                    hazard_val = hazardsvc.get_tornado_hazard_value(hazard_dataset_id, demand_units, location.y,
                                                                    location.x,
                                                                    0)

                dmg_probability = AnalysisUtil.calculate_damage_json(fragility_set, hazard_val)
                demand_type = fragility_set['demandType']
            else:
                dmg_probability['immocc'] = 0.0
                dmg_probability['lifesfty'] = 0.0
                dmg_probability['collprev'] = 0.0

            dmg_interval = AnalysisUtil.calculate_damage_interval(dmg_probability)
            mean_damage = AnalysisUtil.calculate_mean_damage(dmg_weights, dmg_interval)
            mean_damage_dev = AnalysisUtil.calculate_mean_damage_std_deviation(dmg_weights, dmg_weights_std_dev,
                                                                               dmg_interval, mean_damage['meandamage'])

            bldg_results['guid'] = building['properties']['guid']
            bldg_results.update(dmg_probability)
            bldg_results.update(dmg_interval)
            bldg_results.update(mean_damage)
            bldg_results.update(mean_damage_dev)

            bldg_results['hazardtype'] = demand_type
            bldg_results['hazardval'] = hazard_val

            return bldg_results

        except Exception as e:
            # This prints the type, value and stacktrace of error being handled.
            traceback.print_exc()
            print()
            raise e
