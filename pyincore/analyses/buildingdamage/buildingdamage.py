#!/usr/bin/env python3

"""Building Damage Analysis

Usage:
    building_damage.py INVENTORY HAZARD MAPPING DMGRATIO BASEDATASETID EXECUTION
    building_damage.py INVENTORY HAZARD MAPPING DMGRATIO BASEDATASETID EXECUTION THREADS

Options:
    INVENTORY     inventory file in ESRI shapefile
    HAZARD        type/id (e.g. earthquake/59f3315ec7d30d4d6741b0bb)
    MAPPING       fragility mapping id
    DMGRATIO      damage ratio file in CSV
    BASEDATASETID parent of the output file, needed for result ingestion
    EXECUTION     0 - process pool, 1 - thread pool, 2 - sequential
    THREADS       Number of threads/cpus to use


"""
import collections
from pyincore import InsecureIncoreClient, InventoryDataset, DamageRatioDataset, HazardService, FragilityService
from pyincore import GeoUtil, AnalysisUtil
from pyincore.analyses.buildingdamage.buildingutil import BuildingUtil
from docopt import docopt
import os
import csv
import multiprocessing
import concurrent.futures


class BuildingDamage:

    def __init__(self, client, building_path: str, hazard_service: str, mapping_id: str, dmg_ratios: str, exec_type: int
                 , base_datast_id: str=None, num_threads: int=0):
        # TODO determine the file name
        shp_file = None

        for file in os.listdir(building_path):
            if file.endswith(".shp"):
                shp_file = os.path.join(building_path, file)

        building_shp = os.path.abspath(shp_file)

        building_set = InventoryDataset(building_shp)

        # Handle the case where Ergo data has an .mvz
        # In the case of multiple files, DataWolf creates a folder and passes that to the tool
        dmg_ratio = None
        if(os.path.isfile(dmg_ratios)):
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
        hazard_type = hazard_service_split[0]
        hazard_dataset_id = hazard_service_split[1]

        # Create Hazard and Fragility service
        hazardsvc = HazardService(client)
        fragilitysvc = FragilityService(client)

        # damage weights for buildings
        dmg_weights = [
            float(damage_ratios[1]['Mean Damage Factor']),
            float(damage_ratios[2]['Mean Damage Factor']),
            float(damage_ratios[3]['Mean Damage Factor']),
            float(damage_ratios[4]['Mean Damage Factor'])]
        dmg_weights_std_dev = [float(damage_ratios[1]['Deviation Damage Factor']), float(damage_ratios[2]['Deviation Damage Factor']), float(damage_ratios[3]['Deviation Damage Factor']), float(damage_ratios[4]['Deviation Damage Factor'])]

        fragility_sets = fragilitysvc.map_fragilities(mapping_id, building_set.inventory_set, "Non-Retrofit Fragility ID Code")

        buildings = range(0, len(building_set.inventory_set))
        parallelism = self.determine_parallelism_locally(len(building_set.inventory_set), num_threads)
        output = []

        # Determine which type of building damage analysis to run
        if exec_type == 0:
            output = self.building_damage_process_pool(parallelism, buildings, building_set, dmg_weights, dmg_weights_std_dev, fragility_sets, hazardsvc, hazard_dataset_id, hazard_type)
        elif exec_type == 1:
            output = self.building_damage_thread_pool(parallelism, buildings, building_set, dmg_weights, dmg_weights_std_dev, fragility_sets, hazardsvc, hazard_dataset_id, hazard_type)
        else:
            output = self.building_damage_sequential(building_set, dmg_weights, dmg_weights_std_dev, fragility_sets, hazardsvc, hazard_dataset_id, hazard_type)

        # Write Output to csv
        with open('dmg-results.csv', 'w') as csv_file:
            # Write the parent ID at the top of the result data, if it is given
            if base_dataset_id is not None:
                csv_file.write(base_dataset_id + '\n')

            writer = csv.DictWriter(csv_file, dialect="unix", fieldnames=['guid', 'immocc', 'lifesfty', 'collprev', 'insignific', 'moderate', 'heavy', 'complete', 'meandamage', 'mdamagedev', 'hazardtype', 'hazardval'])
            writer.writeheader()
            writer.writerows(output)

    def building_damage_sequential(self, building_set, dmg_weights, dmg_weights_std_dev, fragility_sets, hazardsvc, hazard_dataset_id, hazard_type):
        output = []
        for building in building_set.inventory_set:
            bldg_output = self.building_damage_analysis(building, dmg_weights, dmg_weights_std_dev,
                                                        fragility_sets[building["id"]], hazardsvc, hazard_dataset_id,
                                                        hazard_type)
            output.append(bldg_output)

        return output

    def building_damage_thread_pool(self, parallelism, buildings, building_set, dmg_weights, dmg_weights_std_dev, fragility_sets, hazardsvc, hazard_dataset_id, hazard_type):
        output = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallelism) as executor:
            for id in buildings:
                if building_set.inventory_set[id]["id"] in fragility_sets:
                    future = executor.submit(self.building_damage_analysis, building_set.inventory_set[id], dmg_weights,
                                             dmg_weights_std_dev,
                                             fragility_sets[building_set.inventory_set[id]["id"]],
                                             hazardsvc, hazard_dataset_id, hazard_type)
                    output.append(future.result())
        return output

    def building_damage_process_pool(self, parallelism, buildings, building_set, dmg_weights, dmg_weights_std_dev, fragility_sets, hazardsvc, hazard_dataset_id, hazard_type):
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=parallelism) as executor:
            for id in buildings:
                future = executor.submit(self.building_damage_analysis, building_set.inventory_set[id], dmg_weights,
                                         dmg_weights_std_dev,
                                         fragility_sets[building_set.inventory_set[id]["id"]],
                                         hazardsvc, hazard_dataset_id, hazard_type)
                output.append(future.result())
        return output

    def determine_parallelism_locally(self, number_of_loops, user_defined_parallelism=0):
        '''
        Determine the parallelism on the current compute node
        Args:
            number_of_loops: total number of loops will be executed on current compute node
            user_defined_parallelism: a customized parallelism specified by users
        Returns:
            number_of_cpu: parallelism on current compute node
        '''

        # gets the local cpu number
        number_of_cpu = multiprocessing.cpu_count()
        if number_of_loops > 0:
            if user_defined_parallelism > 0:
                return min(number_of_cpu, number_of_loops, user_defined_parallelism)
            else:
                return min(number_of_cpu, number_of_loops)
        else:
            return number_of_cpu;

    def building_damage_analysis(self, building, dmg_weights, dmg_weights_std_dev, fragility_set, hazardsvc, hazard_dataset_id, hazard_type):
        # print(building)
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
            hazard_val = hazardsvc.get_hazard_value(hazard_dataset_id, hazard_demand_type, demand_units, location.y,
                                                    location.x)
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


if __name__ == '__main__':
    arguments = docopt(__doc__)

    building_path = arguments['INVENTORY']
    hazard_service = arguments['HAZARD']
    mapping_id = arguments['MAPPING']
    dmg_ratios = arguments['DMGRATIO']
    base_dataset_id = arguments['BASEDATASETID']
    exec_type = int(arguments['EXECUTION'])

    num_threads = 0
    # Get number of cpus or threads, if specified
    if arguments['THREADS'] is not None:
        num_threads = int(arguments['THREADS'])

    cred = None
    try:
        with open(".incorepw", 'r') as f:
            cred = f.read().splitlines()

        client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", cred[0])
        BuildingDamage(client, building_path, hazard_service, mapping_id, dmg_ratios, exec_type, base_dataset_id,
                       num_threads)

    except EnvironmentError:
        print("Could not get client credentials")

